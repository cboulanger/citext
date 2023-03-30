#!/usr/bin/env ruby
require 'cgi'
require 'json'

cgi = CGI.new
params = cgi.params

server_file =""
if params.has_key?"file"
    file = params["file"].first
    server_file = File.join('tmp', file.original_filename)
    File.open(server_file, "wb") do |f|
        f << file.read
    end
end

cgi.out("application/json") { {"result":"OK"}.to_json }
