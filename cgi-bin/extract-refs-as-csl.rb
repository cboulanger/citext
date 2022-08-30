#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'

# params
cgi = CGI.new
refs = cgi.params["refs"].first
model_name = cgi.params["model"].first

# find refs in document
if model_name != "default"
    AnyStyle.parser.load_model File.join("Models", model_name, "parser.mod").untaint
end
seqs = AnyStyle.parser.label refs
csl = JSON.pretty_generate AnyStyle.parser.format_csl(seqs)

# return to client
cgi.out("application/json") { csl }
