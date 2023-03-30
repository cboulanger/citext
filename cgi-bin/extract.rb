#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'
cgi = CGI.new
filename = cgi.params["filename"].first
filepath = File.join("tmp", filename)
doc = AnyStyle::Document.open(filepath, tagged:false)
cgi.out("application/json") { doc.to_json }
