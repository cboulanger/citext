require 'rexml'
require 'json'

class Utils
  # split multiple references in sequences, using a very naive heuristic
  # @param [REXML::Document] doc
  # @return [REXML::Document]
  def self.split_multiple_references(doc)
    REXML::XPath.each(doc, '//sequence') do |sequence|
      segs = {}
      curr_sequence = sequence
      sequence.elements.each do |segment|
        seg_name = segment.name
        # this assumes that a new reference sequence starts with author, signal or editor,
        # which should cover most cases but will certainly fail sometimes
        if ["author", "signal", "editor"].include?(seg_name)
          # do we have a minimally complete reference already?
          if segs[:author] && segs[:title] && segs[:date]
            # add new sequence
            curr_sequence = doc.root.add_element 'sequence'
            segs = {}
          end
        end
        if curr_sequence != sequence
          # move segment to new sequence
          sequence.delete_element segment
          curr_sequence.add_element segment
        end
        segs[seg_name.to_sym] = true
      end
    end
    doc
  end

  def self.increment_file_version(file_path)
    file_info_path = "#{file_path}.info"
    file_info = if File.exist? file_info_path
                  JSON.load_file file_info_path
                else
                  {
                    "modified": 0,
                    "version": 0
                  }
                end
    file_info['version'] = (file_info['version'] || 0) + 1
    file_info['modified'] = File.mtime file_path
    File.write file_info_path, file_info.to_json
  end
end

