#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'
require 'fileutils'
require 'nokogiri'
require 'rexml/document'
require 'tempfile'
require_relative '../lib/sse.rb'
require_relative '../lib/utils.rb'

threads = 4
AnyStyle::Finder.defaults[:threads] = threads
AnyStyle::Parser.defaults[:threads] = threads

# params
cgi = CGI.new
model_name = cgi.params['model'].first
target = cgi.params['target'].first
channel_id = cgi.params['channel_id'].first

max_seq_count = 2000 # cgi.params["max_seq_count"] || [1500]).first.to_i

# sse
sse = SSE.new(channel_id)

# merging datasets
merge_datasets_file = '_merge-datasets'

begin

  # get lock
  lock_file = File.join('Dataset', model_name, "lock")
  if File.exist? lock_file
    raise RuntimeError("Training or sync in progress. Try again later.")
  end
  FileUtils.touch(lock_file)

  # finder model
  if target == 'finder' or target == 'both'
    toast = Toast.new(sse, 'info', 'Training finder model')
    dataset_finder_dir = File.join('Dataset', model_name, 'anystyle', 'finder')

    # assemble finder annotations to train on
    files = Dir[File.join(dataset_finder_dir, '*.ttx')]
    merge_finder_datasets_file = File.join(dataset_finder_dir, merge_datasets_file)
    if File.exist? merge_finder_datasets_file
      File.read(merge_finder_datasets_file).split().each do |dataset|
        new_files = Dir[File.join('Dataset', dataset, 'anystyle', 'finder', '*.ttx')]
        STDERR.puts "Merging #{new_files.length} files from parser dataset #{dataset}"
        files = (files + new_files).uniq
      end
    end
    toast.show "Using dataset with #{files.length} sequences, please wait..."
    AnyStyle.finder.train files
    finder_model_path = File.join(Dir.pwd, 'Models', model_name, 'finder.mod')
    AnyStyle.finder.model.save finder_model_path
    Utils.increment_file_version finder_model_path
    toast.close
    unless target == 'both'
      Toast.new(sse, 'success', 'Finder model training completed.').show('The new model can now be used.')
    end
  end

  # parser model
  if target == 'parser' or target == 'both'
    toast = Toast.new(sse, 'info', 'Training parser model')
    # assemble parser annotations to train on
    dataset_parser_dir = File.join(Dir.pwd, 'Dataset', model_name, 'anystyle', 'parser')
    files = Dir[File.join(dataset_parser_dir, '*.xml')]
    merge_parser_datasets_file = File.join(dataset_parser_dir, merge_datasets_file)
    if File.exist? merge_parser_datasets_file
      File.read(merge_parser_datasets_file).split().each do |dataset|
        new_files = Dir[File.join('Dataset', dataset, 'anystyle', 'parser', '*.xml')]
        STDERR.puts "Merging #{new_files.length} files from parser dataset #{dataset}"
        files = (files + new_files).uniq
      end
    end
    doc = Nokogiri::XML::Document.new { |config| config.strict }
    root = doc.add_child(Nokogiri::XML::Node.new 'dataset', doc)
    seq_count = 0
    files.each do |file_path|
      STDERR.puts 'Importing sequences from ' + file_path
      doc2 = File.open(file_path) { |f| Nokogiri::XML(f) }
      count_nodes_before = doc2.xpath('count(//sequence)')
      # remove all <ignore> nodes
      doc2.xpath('//ignore').map(&:remove)
      # here, we need to filter out duplicate references, maybe by caching author/title/date data
      break unless doc2.xpath('//sequence').each do |seq|
        seq_count += 1
        if seq_count > max_seq_count
          STDERR.puts "Max number of #{max_seq_count} sequences reached."
          break
        end
        root.add_child(seq)
      end
    end

    # remove blank & empty nodes
    doc.xpath('//text()').find_all { |t| t.to_s.strip == '' }.map(&:remove)
    doc.xpath('//*[not(normalize-space())]').map(&:remove)
    num_sequences = doc.xpath('count(//sequence)')
    # write a new combined XML
    tmp_xml_path = File.join(Dir.pwd, 'tmp', model_name + '-parser.xml')
    doc = REXML::Document.new(doc.to_xml())
    formatter = REXML::Formatters::Pretty.new(2)
    formatter.width = 10000 # no wrap
    formatter.compact = true
    fp = File.open(tmp_xml_path, 'w')
    formatter.write(doc, fp)
    fp.close()
    doc = nil
    doc = REXML::Document.new File.new(tmp_xml_path)
    STDERR.puts "#{tmp_xml_path} seems legit"
    toast.show "Using dataset with #{num_sequences.to_i} sequences, please wait..."
    AnyStyle.parser.train Wapiti::Dataset.open(tmp_xml_path)
    parser_model_path = File.join(Dir.pwd, 'Models', model_name, 'parser.mod')
    AnyStyle.parser.model.save parser_model_path
    Utils.increment_file_version parser_model_path
    toast.close
    unless target == 'both'
      Toast.new(sse, 'success', 'Parser model training completed.').show('The new model can now be used.')
    end
  end
  if target == 'both'
    Toast.new(sse, 'success', 'Model training completed.').show('The new models can now be used.')
  end
  response = { result: 'OK' }
rescue => e
  STDERR.puts "Error: #{$!}\n\t#{e.backtrace.join("\n\t")}"
  response = { error: e.message }
ensure
  if File.exist? lock_file
    File.delete(lock_file)
   end
end

# return to client
cgi.out('application/json') { response.to_json }

# the following workarounds do not longer seem necessary, but can be reactivated if
# we encounter a wapiti segmentation fault again
# work around wapiti bug by removing leading or trailing <note>
# doc2.xpath("//sequence/*[1][name()='note']").map(&:remove)
# doc2.xpath("//sequence/*[last()][name()='note']").map(&:remove)
# remove all low quality sequences (i.e. nodes that have fewer than 3 child nodes)
# doc2.xpath("//sequence[count(./*) < 3 ]").map(&:remove)
# remove all sequences that don't at least have an author/editor, title or date
# doc2.xpath("//sequence[not(./author) and not(./editor)]").map(&:remove)
# doc2.xpath("//sequence[not(./date) and not(./title)]").map(&:remove)
# count_nodes_after = doc2.xpath("count(//sequence)")
# count_nodes_removed = count_nodes_before - count_nodes_after
# STDERR.puts "After removing #{count_nodes_removed.to_i.to_s} sequences, #{count_nodes_after.to_i.to_s} sequences can be merged."

