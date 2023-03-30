#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'
require_relative '../lib/utils.rb'

# params
cgi = CGI.new
refs = cgi.params["refs"].first
model_name = cgi.params["model"].first

# find refs in document
begin
    if model_name != "default"
        AnyStyle.parser.load_model File.join("Models", model_name, "parser.mod")
    end
    seqs = AnyStyle.parser.label refs
    response = seqs.to_xml(indent:2)
rescue => e
    STDERR.puts "Error: #{$!}\n\t#{e.backtrace.join("\n\t")}"
    response = { error: e.message }
end

# return to client
cgi.out("application/json") { response.to_json }
