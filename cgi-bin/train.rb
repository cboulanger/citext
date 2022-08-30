#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'

threads = 4
AnyStyle::Finder.defaults[:threads] = threads
AnyStyle::Parser.defaults[:threads] = threads

# params
cgi = CGI.new
model_name = cgi.params["model"].first

# finder model
files = Dir[File.join(Dir.pwd, "Dataset", model_name, "finder", "*.ttx")].map(&:untaint)
AnyStyle.finder.train files

finder_model_path = File.join(Dir.pwd, "Models", model_name, "finder.mod").untaint
AnyStyle.finder.model.save finder_model_path

# parser model
ds_path = File.join( Dir.pwd, "Dataset", model_name,"parser", "parser.xml" ).untaint
AnyStyle.parser.train Wapiti::Dataset.open(ds_path)

parser_model_path = File.join(Dir.pwd, "Models",  model_name, "parser.mod").untaint
AnyStyle.parser.model.save parser_model_path

# return to client
cgi.out("application/json") { files.to_json }
