#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'
require 'nokogiri'
require "rexml/document"
require_relative '../lib/sse.rb'

threads = 4
AnyStyle::Finder.defaults[:threads] = threads
AnyStyle::Parser.defaults[:threads] = threads

# params
cgi = CGI.new
model_name = cgi.params["model"].first
target = cgi.params["target"].first
channel_id = cgi.params["channel_id"].first

max_seq_count = 2000 #cgi.params["max_seq_count"] || [1500]).first.to_i

# sse
sse = SSE.new(channel_id)

# finder model
if target == "finder" or target == "both"
  if  !Dir.exist? File.join(Dir.pwd, "Dataset", model_name, "anystyle", "finder")
    cgi.out("application/json") { {"error":"No finder model exists for #{model_name}"}.to_json }
    exit(0)
  end
  sse.push_event("info", "Finder Model: Training, please wait...")

  files = Dir[File.join(Dir.pwd, "Dataset", model_name, "anystyle", "finder", "*.ttx")].map(&:untaint)
  AnyStyle.finder.train files
  finder_model_path = File.join(Dir.pwd, "Models", model_name, "finder.mod").untaint
  AnyStyle.finder.model.save finder_model_path
  sse.push_event("info", "Finder Model: Training is done. The new parser model can now be used.")
end

# parser model
if target == "parser" or target == "both"
  if target = "both"
    sse.push_event("info", "")
  end
  sse.push_event("info", "Parser Model: Training, please wait...")
  files = Dir[File.join(Dir.pwd, "Dataset", model_name, "anystyle", "parser", "*.xml")].map(&:untaint)
  doc = Nokogiri::XML::Document.new { |config| config.strict }
  root = doc.add_child(Nokogiri::XML::Node.new "dataset", doc)
  seq_count = 0
  files.each do |file_path|
    STDERR.puts "Importing sequences from " + file_path
    doc2 = File.open(file_path) { |f| Nokogiri::XML(f) }
    count_nodes_before = doc2.xpath("count(//sequence)")
    # remove all <ignore> nodes
    doc2.xpath("//ignore").map(&:remove)
    # work around wapiti bug by removing leading or trailing <note>
    doc2.xpath("//sequence/*[1][name()=='note']").map(&:remove)
    doc2.xpath("//sequence/*[last()][name()=='note']").map(&:remove)
    if model_name == "fn-segmentation" # TODO remove hardcoding, this needs to be configured somehow, maybe with a model config file
      # remove all low quality sequences (i.e. nodes that have fewer than 3 child nodes)
      doc2.xpath("//sequence[count(./*) < 3 ]").map(&:remove)
      # remove all sequences that don't at least have an author/editor, title or date
      doc2.xpath("//sequence[not(./author) and not(./editor)]").map(&:remove)
      doc2.xpath("//sequence[not(./date) and not(./title)]").map(&:remove)
      count_nodes_after = doc2.xpath("count(//sequence)")
      count_nodes_removed = count_nodes_before - count_nodes_after
      STDERR.puts "After removing #{count_nodes_removed.to_i.to_s} low quality sequences, merging #{count_nodes_after.to_i.to_s} sequences from #{file_path}"
    end
    break unless doc2.xpath("//sequence").each do |seq|
      seq_count += 1
      if seq_count > max_seq_count
        STDERR.puts "Max number of #{max_seq_count} sequences reached."
        break
      end
      root.add_child(seq)
    end
  end

  # remove blank & empty nodes
  doc.xpath('//text()').find_all {|t| t.to_s.strip == ''}.map(&:remove)
  doc.xpath('//*[not(normalize-space())]').map(&:remove)
  STDERR.puts "Training model with #{doc.xpath('count(//sequence)').to_i.to_s} sequences"
  tmp_xml_path = File.join(Dir.pwd, "tmp", model_name + "-parser.xml")
  doc = REXML::Document.new(doc.to_xml())
  formatter = REXML::Formatters::Pretty.new(2)
  formatter.width = 10000 # no wrap
  formatter.compact = true
  formatter.write(doc, File.open(tmp_xml_path, "w"))
  doc = nil
  AnyStyle.parser.train Wapiti::Dataset.open(tmp_xml_path)
  parser_model_path = File.join(Dir.pwd, "Models",  model_name, "parser.mod").untaint
  AnyStyle.parser.model.save parser_model_path
  sse.push_event("info", "Parser Model: Training is done. The new parser model can now be used.")
end

# return to client
cgi.out("application/json") { {"result":"OK"}.to_json }
