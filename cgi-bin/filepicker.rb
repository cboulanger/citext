#!/usr/bin/env ruby
# frozen_string_literal: true

require 'cgi'
require 'json'

# params
cgi = CGI.new
model_name = cgi.params['model']&.first&.gsub('\.\.', '')
model_type = cgi.params['type']&.first&.gsub('\.\.', '')
delete_file = cgi.params['delete']&.first&.gsub('\.\.', '')

def li(path, model_name, model_type)
  <<~HTML
    <li>
      <a href='#' onclick='select_file(\"#{path}\")'>#{File.basename(path)}</a>&nbsp;
      [ <a href='?model=#{model_name}&type=#{model_type}&delete=#{path}'>x</a> ]
    </li>
  HTML
end

def create_document(finder_files, parser_files, model_name, model_type)
  <<~HTML
    <!DOCTYPE HTML>
    <html>
        <head>
        <script>
            function select_file(name) {
                window.opener.postMessage(name||'','*')
                setTimeout( ()=> window.close(), 500)
            }
        </script>
        <style>
            body {
                font-family: 'Helvetica Neue',Helvetica,Arial,sans-serif;
                font-size: 14px;
                line-height: 1.42857143;
                color: #333;
            }
            td, th {
                vertical-align: top;
                text-align: left;
                white-space: nowrap;
            }
        </style>
        </head>
        <body>
            <h3>Select a file</h3>
            <button type='button' onclick='select_file()'>Close</button>
            <table>
                <tr><th>Finder</th><th>Parser</th></tr>
                <tr>
                    <td><ul>#{finder_files.map { |p| li(p, model_name, model_type) }.join}</ul></td>
                    <td><ul>#{parser_files.map { |p| li(p, model_name, model_type) }.join}</ul></td>
                </tr>
            </table>
            <button type='button' onclick='select_file()'>Close</button>
        </body>
    </html>
  HTML
end

model_dir = File.join('Dataset', model_name)
finder_files = Dir.glob("#{model_dir}/anystyle/finder/*").select { |f| f.match(/\.(ttx|txt)$/) }
parser_files = Dir.glob("#{model_dir}/anystyle/parser/*").select { |f| f.match(/\.xml$/) }

html = if !model_name || !model_type || !Dir.exist?(model_dir)
         'Invalid request'
       elsif delete_file
         if delete_file.start_with? '!'
           do_delete = true
           file_path = delete_file[1..]
         else
           file_path = delete_file
         end
         if !file_path.start_with? model_dir
           'Forbidden.'
         elsif !File.exist? file_path
           "#{file_path} does not exist."
         elsif !do_delete
           <<~HTML
              <p>Really delete "#{File.basename file_path}"?</p>
              <b><a href='?model=#{model_name}&type=#{model_type}&delete=!#{file_path}'>Delete</a></b>&nbsp;
              <a href='?model=#{model_name}&type=#{model_type}'>Cancel</a>&nbsp;
           HTML
         else
           deleted_file_path = "#{file_path}.deleted"
           File.delete deleted_file_path if File.exists? deleted_file_path
           File.rename file_path, deleted_file_path
           file_info_path = "#{file_path}.info"
           if File.exist? file_info_path
             file_info = JSON.parse(File.read(file_info_path))
             file_info['deleted'] = true
             file_info['modified'] = Time.now.to_f
             File.write file_info_path, JSON.dump(file_info)
            end
           <<~HTML
              <p>"#{File.basename file_path}" was deleted.</p>
              <b><a href='?model=#{model_name}&type=#{model_type}'>Continue</a></b>
           HTML
         end
       else
         create_document finder_files, parser_files, model_name, model_type
       end

cgi.out('type' => 'text/html', 'charset' => 'utf-8') { html }
