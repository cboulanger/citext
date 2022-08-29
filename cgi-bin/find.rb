#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'

# params
cgi = CGI.new
file_name = cgi.params["filename"].first
model_name = cgi.params["model"].first
file_path = File.join("tmp", file_name).untaint

# find refs in document
AnyStyle.finder.load_model File.join("Models", model_name, "finder.mod").untaint
ttx = AnyStyle.finder.find(file_path, format: :wapiti)[0].to_s(tagged:true).gsub(/\u00AD ?/, "")

# return to client
cgi.out("application/json") { ttx.to_json }
