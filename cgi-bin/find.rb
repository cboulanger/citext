#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'

# params
cgi = CGI.new
file_name = cgi.params["filename"].first
model_name = cgi.params["model"].first
file_path = File.join("tmp", file_name)

if ! File.exists?(file_path)
    response = {error: "File #{file_name} cannot be found."}
else
    begin
        # find refs in document
        if model_name != "default"
            AnyStyle.finder.load_model File.join("Models", model_name, "finder.mod")
        end
        response = AnyStyle.finder.find(file_path, format: :wapiti)[0].to_s(tagged:true)
    rescue => e
        STDERR.puts "Error: #{$!}\n\t#{e.backtrace.join("\n\t")}"
        response = {
            error: e.message
        }
    end
end

# return to client
cgi.out("application/json") { response.to_json }
