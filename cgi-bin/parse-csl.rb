#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'
require 'rexml'
require_relative '../lib/utils.rb'

# params
cgi = CGI.new
seq = cgi.params["seq"].first
model_name = cgi.params["model"].first

# find refs in document
if model_name != "default"
  AnyStyle.parser.load_model File.join("Models", model_name, "parser.mod")
end

doc = REXML::Document.new seq.gsub(/\n */,"")
doc = Utils.split_multiple_references(doc)

seqs = Wapiti::Dataset.parse(doc)
csl =  AnyStyle.parser.format_csl(seqs)

# fix missing/incorrect types
csl.map! do |item|
  if item[:type] == nil
    if item[:issued] and ! item["container-title"]
      item[:type] = "book"
    end
  end
  if item[:editor] or item["publisher-place"] or item[:publisher] or item[:edition]
    if item["container-title"] or item[:author]
      item[:type] = "chapter"
    else
      item[:type] = "book"
    end
  end
  item
end

# filter invalid items
csl.select! { |item| item.size() > 1 }

# clean up and return
csl_json = JSON.pretty_generate csl
csl_json = csl_json.gsub(/&amp;/,"&").gsub(/&amp;/,"&")
cgi.out("application/json") { csl_json }
