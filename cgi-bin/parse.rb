#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'

# params
cgi = CGI.new
refs = cgi.params["refs"].first
model_name = cgi.params["model"].first

# find refs in document
AnyStyle.parser.load_model File.join("Models", model_name, "parser.mod").untaint
seqs = AnyStyle.parser.label refs
labelled_refs = seqs.to_xml(indent:2)
# return to client
cgi.out("application/json") { labelled_refs.to_json }
