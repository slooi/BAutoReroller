import socket
import struct
import time
from pathlib import Path


class H264StreamProcessor:
    def __init__(self, host="127.0.0.1", port=1234):
        self.host = host
        self.port = port
        self.nal_units = []
        self.frame_count = 0

    def find_nal_units(self, data):
        """Find NAL units in H.264 AnnexB format"""
        nal_units = []
        i = 0

        while i < len(data) - 4:
            # Look for start code: 00 00 00 01
            if (
                data[i] == 0x00
                and data[i + 1] == 0x00
                and data[i + 2] == 0x00
                and data[i + 3] == 0x01
            ):

                start_pos = i
                i += 4  # Skip start code

                if i < len(data):
                    nal_type = data[i] & 0x1F

                    # Find next start code or end of data
                    end_pos = len(data)
                    for j in range(i, len(data) - 4):
                        if (
                            data[j] == 0x00
                            and data[j + 1] == 0x00
                            and data[j + 2] == 0x00
                            and data[j + 3] == 0x01
                        ):
                            end_pos = j
                            break

                    nal_units.append(
                        {
                            "type": nal_type,
                            "start": start_pos,
                            "end": end_pos,
                            "size": end_pos - start_pos,
                            "data": data[start_pos:end_pos],
                        }
                    )

                    i = end_pos
                else:
                    i += 1
            else:
                i += 1

        return nal_units

    def get_nal_type_name(self, nal_type):
        """Get human-readable NAL unit type name"""
        nal_types = {
            1: "Coded slice of a non-IDR picture",
            2: "Coded slice data partition A",
            3: "Coded slice data partition B",
            4: "Coded slice data partition C",
            5: "Coded slice of an IDR picture",
            6: "Supplemental enhancement information (SEI)",
            7: "Sequence parameter set (SPS)",
            8: "Picture parameter set (PPS)",
            9: "Access unit delimiter",
            10: "End of sequence",
            11: "End of stream",
            12: "Filler data",
        }
        return nal_types.get(nal_type, f"Unknown ({nal_type})")

    def analyze_stream(self, output_file="output.h264", max_frames=100):
        """Connect to scrcpy server and analyze the H.264 stream"""

        print(f"[*] Connecting to {self.host}:{self.port}")

        with socket.create_connection((self.host, self.port)) as sock:
            sock.settimeout(1.0)
            print("[*] Connected to scrcpy server")

            buffer = bytearray()
            frame_data = []

            with open(output_file, "wb") as f:
                try:
                    while self.frame_count < max_frames:
                        try:
                            data = sock.recv(4096)
                            if not data:
                                print("[!] Disconnected")
                                break

                            buffer.extend(data)
                            f.write(data)

                            # Process complete NAL units from buffer
                            self.process_buffer(buffer, frame_data)

                            # Show hex data for first few packets
                            if len(frame_data) < 5:
                                hex_data = " ".join(f"{b:02X}" for b in data[:32])
                                print(f"[Frame {len(frame_data)}] {hex_data}...")

                        except socket.timeout:
                            continue

                except KeyboardInterrupt:
                    print("\n[!] Interrupted by user")

            print(f"\n[*] Analysis complete:")
            print(f"    - Total frames captured: {self.frame_count}")
            print(f"    - Total NAL units: {len(self.nal_units)}")
            print(f"    - Output file: {output_file}")

            self.print_nal_summary()
            return frame_data

    def process_buffer(self, buffer, frame_data):
        """Process buffer to extract complete NAL units"""
        nal_units = self.find_nal_units(bytes(buffer))

        for nal in nal_units:
            self.nal_units.append(nal)

            # Check if this is a frame (IDR or non-IDR slice)
            if nal["type"] in [1, 5]:  # Non-IDR or IDR slice
                self.frame_count += 1
                frame_data.append(
                    {
                        "frame_num": self.frame_count,
                        "nal_type": nal["type"],
                        "size": nal["size"],
                        "is_keyframe": nal["type"] == 5,
                    }
                )

                print(
                    f"[Frame {self.frame_count}] Type: {self.get_nal_type_name(nal['type'])}, Size: {nal['size']} bytes"
                )

        # Keep only unprocessed data in buffer
        if nal_units:
            last_nal_end = nal_units[-1]["end"]
            buffer[:last_nal_end] = []

    def print_nal_summary(self):
        """Print summary of NAL units found"""
        nal_type_counts = {}

        for nal in self.nal_units:
            nal_type = nal["type"]
            if nal_type not in nal_type_counts:
                nal_type_counts[nal_type] = 0
            nal_type_counts[nal_type] += 1

        print("\n[*] NAL Unit Summary:")
        for nal_type, count in sorted(nal_type_counts.items()):
            print(f"    - {self.get_nal_type_name(nal_type)}: {count}")

    def save_frame_info(self, frame_data, filename="frame_info.txt"):
        """Save frame information to text file"""
        with open(filename, "w") as f:
            f.write("Frame Analysis Report\n")
            f.write("=" * 50 + "\n\n")

            keyframe_count = sum(1 for frame in frame_data if frame["is_keyframe"])
            f.write(f"Total Frames: {len(frame_data)}\n")
            f.write(f"Keyframes (I-frames): {keyframe_count}\n")
            f.write(f"P-frames: {len(frame_data) - keyframe_count}\n\n")

            f.write("Frame Details:\n")
            f.write("-" * 50 + "\n")

            for frame in frame_data:
                frame_type = "I-frame" if frame["is_keyframe"] else "P-frame"
                f.write(
                    f"Frame {frame['frame_num']:3d}: {frame_type:8s} | Size: {frame['size']:6d} bytes\n"
                )

        print(f"[*] Frame info saved to {filename}")


def main():
    processor = H264StreamProcessor()

    print("H.264 Stream Analyzer")
    print("=" * 50)
    print("This tool will:")
    print("1. Connect to scrcpy server on localhost:1234")
    print("2. Capture and analyze H.264 stream")
    print("3. Save raw H.264 data to output.h264")
    print("4. Generate analysis report")
    print()

    # Start analysis
    frame_data = processor.analyze_stream(max_frames=5000)

    # Save detailed frame info
    processor.save_frame_info(frame_data)

    print("\n" + "=" * 50)
    print("Analysis complete! Files generated:")
    print("- output.h264: Raw H.264 stream data")
    print("- frame_info.txt: Detailed frame analysis")
    print("\nYou can now load 'output.h264' in the HTML viewer")
    print("or use VLC with: vlc --demux=h264 output.h264")


if __name__ == "__main__":
    main()
