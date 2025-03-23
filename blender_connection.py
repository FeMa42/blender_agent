import socket
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderConnection")


class BlenderConnection:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """Connect to the Blender addon socket server"""
        if self.socket:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {str(e)}")
            self.socket = None
            return False

    def disconnect(self):
        """Disconnect from the Blender addon"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Blender: {str(e)}")
            finally:
                self.socket = None
                logger.info("Disconnected from Blender")

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        # Use a consistent timeout value
        sock.settimeout(15.0)

        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # If we get an empty chunk, the connection might be closed
                        if not chunks:  # If we haven't received anything yet, this is an error
                            raise Exception(
                                "Connection closed before receiving any data")
                        break

                    chunks.append(chunk)

                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        # If we get here, it parsed successfully
                        logger.debug(
                            f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    # If we hit a timeout during receiving, break the loop and try to use what we have
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(
                        f"Socket connection error during receive: {str(e)}")
                    raise  # Re-raise to be handled by the caller
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise

        # If we get here, we either timed out or broke out of the loop
        # Try to use what we have
        if chunks:
            data = b''.join(chunks)
            logger.debug(
                f"Returning data after receive completion ({len(data)} bytes)")
            try:
                # Try to parse what we have
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                # If we can't parse it, it's incomplete
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type, params=None):
        """Send a command to Blender and return the response"""
        if not self.socket and not self.connect():
            raise ConnectionError("Not connected to Blender")

        command = {
            "type": command_type,
            "params": params or {}
        }

        try:
            # Log the command being sent (omit potentially large param values)
            param_keys = list(params.keys()) if params else []
            logger.info(
                f"Sending command: {command_type} with params: {param_keys}")

            # Send the command
            self.socket.sendall(json.dumps(command).encode('utf-8'))
            logger.debug(f"Command sent, waiting for response...")

            # Set a timeout for receiving
            self.socket.settimeout(15.0)

            # Receive the response using the improved receive_full_response method
            response_data = self.receive_full_response(self.socket)
            logger.debug(f"Received {len(response_data)} bytes of data")

            response = json.loads(response_data.decode('utf-8'))
            logger.debug(
                f"Response parsed, status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Blender error: {response.get('message')}")
                raise Exception(response.get(
                    "message", "Unknown error from Blender"))

            return response.get("result", {})
        except socket.timeout:
            logger.error(
                "Socket timeout while waiting for response from Blender")
            # Just invalidate the current socket so it will be recreated next time
            self.socket = None
            raise Exception(
                "Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.socket = None
            raise Exception(f"Connection to Blender lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            # Try to log what was received
            if 'response_data' in locals() and response_data:
                logger.error(
                    f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            self.socket = None
            raise Exception(f"Communication error with Blender: {str(e)}")

    def get_polyhaven_status(self):
        """Check if PolyHaven integration is enabled in Blender"""
        try:
            result = self.send_command("get_polyhaven_status")
            return result
        except Exception as e:
            logger.error(f"Error checking PolyHaven status: {str(e)}")
            return {"enabled": False, "message": str(e)}

    def get_hyper3d_status(self):
        """Check if Hyper3D Rodin integration is enabled in Blender"""
        try:
            result = self.send_command("get_hyper3d_status")
            return result
        except Exception as e:
            logger.error(f"Error checking Hyper3D status: {str(e)}")
            return {"enabled": False, "message": str(e)}
