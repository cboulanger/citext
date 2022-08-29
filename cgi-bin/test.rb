#!/usr/bin/ruby
require 'cgi'
require 'json'
cgi = CGI.new
cgi.out("application/json") { {"result":"OK"}.to_json }
