require 'json'
require 'socket'

class SSE

  def initialize(channel_id)
    @channel_id = channel_id
    @port = File.read(File.join(Dir.pwd, "tmp", channel_id)).to_i
    STDERR.write("Connecting to channel #{@channel_id} via port #{@port.to_s}...\n")
  end

  def push_event(event_name, event_data)
    event = {
      "name": event_name,
      "data": event_data
    }
    # debug
    STDERR.puts("SSE (##{@channel_id}): #{event_name} -> '#{event_data}'")
    # connect to event server and send event
    s = TCPSocket.new '', @port
    s.send event.to_json, 0
    s.close()
  end
end

class Toast

  def initialize(sse, type, title)
    case type
    in 'success' | 'info' | 'warning' | 'error'
      @sse = sse
      @type = type
      @title = title
    else
      raise "Invalid type #{type}"
    end
  end

  def show(message)
    @sse.push_event(@type, "#{@title}:#{message}")
  end

  def close()
    @sse.push_event(@type, "#{@title}:")
  end
end
