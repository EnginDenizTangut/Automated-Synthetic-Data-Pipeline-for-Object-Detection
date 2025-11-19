import bisect
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class DataQuality(Enum):
    VALID = "valid"  
    CORRUPTED = "corrupted"  
    INTERPOLATED = "interpolated"  

@dataclass
class DataPoint:
    timestamp: float  
    value: Any  
    source: str  

    def __repr__(self):
        return f"DataPoint(t={self.timestamp}ms, value={self.value}, source={self.source})"

@dataclass
class AlignedPair:
    video_timestamp: float
    video_value: Any
    sensor_timestamp: float
    sensor_value: Any
    time_difference: float  
    quality: DataQuality
    interpolation_used: bool = False  

    def __repr__(self):
        return (f"AlignedPair(video_t={self.video_timestamp}ms, "
                f"sensor_t={self.sensor_timestamp}ms, "
                f"diff={self.time_difference:.2f}ms, "
                f"quality={self.quality.value})")

class TemporalAligner:

    def __init__(self, 
                 sensor_data: List[DataPoint],
                 max_gap_threshold: float = 50.0):
        self.sensor_data = sorted(sensor_data, key=lambda x: x.timestamp)
        self.sensor_timestamps = [d.timestamp for d in self.sensor_data]
        self.max_gap_threshold = max_gap_threshold

        self.stats = {
            'total_alignments': 0,
            'valid_alignments': 0,
            'corrupted_alignments': 0,
            'interpolated_alignments': 0
        }

    def find_nearest_neighbor(self, target_timestamp: float) -> Tuple[int, float]:
        if not self.sensor_timestamps:
            raise ValueError("Sensor data is empty!")

        idx = bisect.bisect_left(self.sensor_timestamps, target_timestamp)

        candidates = []

        if idx > 0:
            left_idx = idx - 1
            left_diff = abs(target_timestamp - self.sensor_timestamps[left_idx])
            candidates.append((left_idx, left_diff))

        if idx < len(self.sensor_timestamps):
            right_idx = idx
            right_diff = abs(target_timestamp - self.sensor_timestamps[right_idx])
            candidates.append((right_idx, right_diff))

        best_idx, best_diff = min(candidates, key=lambda x: x[1])
        return best_idx, best_diff

    def interpolate(self, 
                    timestamp: float,
                    before_idx: int,
                    after_idx: int) -> Any:
        before = self.sensor_data[before_idx]
        after = self.sensor_data[after_idx]

        if isinstance(before.value, (int, float)) and isinstance(after.value, (int, float)):
            t1, v1 = before.timestamp, before.value
            t2, v2 = after.timestamp, after.value

            if t2 == t1:
                return v1

            ratio = (timestamp - t1) / (t2 - t1)
            interpolated = v1 + (v2 - v1) * ratio
            return interpolated
        else:

            if abs(timestamp - before.timestamp) < abs(timestamp - after.timestamp):
                return before.value
            else:
                return after.value

    def align(self, 
              video_data: List[DataPoint],
              use_interpolation: bool = True) -> List[AlignedPair]:
        aligned_pairs = []

        for video_point in video_data:

            nearest_idx, time_diff = self.find_nearest_neighbor(video_point.timestamp)
            nearest_sensor = self.sensor_data[nearest_idx]

            quality = DataQuality.VALID
            interpolation_used = False
            sensor_timestamp = nearest_sensor.timestamp
            sensor_value = nearest_sensor.value

            if time_diff > self.max_gap_threshold:
                quality = DataQuality.CORRUPTED
                self.stats['corrupted_alignments'] += 1
            else:

                if use_interpolation and time_diff > 0:

                    before_idx = nearest_idx - 1 if nearest_idx > 0 else None
                    after_idx = nearest_idx + 1 if nearest_idx < len(self.sensor_data) - 1 else None

                    if before_idx is not None and after_idx is not None:
                        before = self.sensor_data[before_idx]
                        after = self.sensor_data[after_idx]

                        if before.timestamp <= video_point.timestamp <= after.timestamp:

                            gap_between_sensors = after.timestamp - before.timestamp

                            if gap_between_sensors > self.max_gap_threshold:

                                quality = DataQuality.CORRUPTED
                                self.stats['corrupted_alignments'] += 1

                                sensor_timestamp = nearest_sensor.timestamp
                                sensor_value = nearest_sensor.value
                            else:

                                sensor_value = self.interpolate(video_point.timestamp, before_idx, after_idx)
                                sensor_timestamp = video_point.timestamp  
                                quality = DataQuality.INTERPOLATED
                                interpolation_used = True
                                self.stats['interpolated_alignments'] += 1
                        else:

                            self.stats['valid_alignments'] += 1
                    else:

                        self.stats['valid_alignments'] += 1
                else:

                    self.stats['valid_alignments'] += 1

            pair = AlignedPair(
                video_timestamp=video_point.timestamp,
                video_value=video_point.value,
                sensor_timestamp=sensor_timestamp,
                sensor_value=sensor_value,
                time_difference=time_diff,
                quality=quality,
                interpolation_used=interpolation_used
            )

            aligned_pairs.append(pair)
            self.stats['total_alignments'] += 1

        return aligned_pairs

    def get_statistics(self) -> Dict[str, Any]:
        total = max(1, self.stats['total_alignments'])  
        return {
            **self.stats,
            'sensor_data_count': len(self.sensor_data),
            'max_gap_threshold': self.max_gap_threshold,
            'valid_percentage': (self.stats['valid_alignments'] / total) * 100,
            'corrupted_percentage': (self.stats['corrupted_alignments'] / total) * 100,
            'interpolated_percentage': (self.stats['interpolated_alignments'] / total) * 100
        }

def generate_sample_data() -> Tuple[List[DataPoint], List[DataPoint]]:
    video_data = []
    sensor_data = []

    video_start = 100.0
    video_interval = 1000.0 / 30.0  

    for i in range(10):  
        timestamp = video_start + i * video_interval
        video_data.append(DataPoint(
            timestamp=timestamp,
            value=f"kamera_karesi_{i+1}",
            source="video"
        ))

    sensor_start = 105.0  
    sensor_interval = 1000.0 / 100.0  

    for i in range(30):  
        timestamp = sensor_start + i * sensor_interval

        speed = 5.0 + (i % 5) * 0.5  

        sensor_data.append(DataPoint(
            timestamp=timestamp,
            value=speed,
            source="sensor"
        ))

    sensor_data = [d for d in sensor_data if not (200 <= d.timestamp <= 250)]

    return video_data, sensor_data

def print_alignment_results(aligned_pairs: List[AlignedPair], stats: Dict[str, Any]):
    print("\n" + "=" * 100)
    print("TEMPORAL ALIGNMENT RESULTS")
    print("=" * 100)

    print(f"\n📊 STATISTICS:")
    print(f"  • Total Alignments: {stats['total_alignments']}")
    print(f"  • Valid: {stats['valid_alignments']} ({stats['valid_percentage']:.1f}%)")
    print(f"  • Corrupted: {stats['corrupted_alignments']} ({stats['corrupted_percentage']:.1f}%)")
    print(f"  • Interpolated: {stats['interpolated_alignments']} ({stats['interpolated_percentage']:.1f}%)")
    print(f"  • Sensor Data Count: {stats['sensor_data_count']}")
    print(f"  • Max Gap Threshold: {stats['max_gap_threshold']}ms")

    print(f"\n📋 ALIGNED PAIRS:")
    print("-" * 100)
    print(f"{'Video (ms)':<12} {'Video Value':<20} {'Sensor (ms)':<12} {'Sensor Value':<15} "
          f"{'Diff (ms)':<12} {'Quality':<15} {'Interp':<8}")
    print("-" * 100)

    for pair in aligned_pairs:
        quality_icon = {
            DataQuality.VALID: "✅",
            DataQuality.CORRUPTED: "⚠️",
            DataQuality.INTERPOLATED: "🔗"
        }.get(pair.quality, "❓")

        interp_icon = "✓" if pair.interpolation_used else "-"

        sensor_val_str = f"{pair.sensor_value:.2f}" if isinstance(pair.sensor_value, (int, float)) else str(pair.sensor_value)

        print(f"{pair.video_timestamp:<12.2f} {str(pair.video_value):<20} "
              f"{pair.sensor_timestamp:<12.2f} {sensor_val_str:<15} "
              f"{pair.time_difference:<12.2f} {quality_icon} {pair.quality.value:<12} {interp_icon:<8}")

    print("-" * 100)

    corrupted = [p for p in aligned_pairs if p.quality == DataQuality.CORRUPTED]
    if corrupted:
        print(f"\n⚠️  CORRUPTED DATA DETECTED ({len(corrupted)} entries):")
        for pair in corrupted:
            print(f"  • Video: {pair.video_timestamp:.2f}ms - "
                  f"Nearest sensor: {pair.sensor_timestamp:.2f}ms "
                  f"(Diff: {pair.time_difference:.2f}ms > {stats['max_gap_threshold']}ms)")

def main():
    print("=" * 100)
    print("TEMPORAL ALIGNER - Orbifold Align Engine Simulation")
    print("=" * 100)
    print("\n🎯 Scenario:")
    print("  • Source A: 30 FPS Video (one frame every ~33.33ms)")
    print("  • Source B: 100 Hz Sensor (one reading every 10ms)")
    print("  • Video starts at 100ms, Sensor starts at 105ms (5ms offset)")
    print("  • Sensor data missing between 200-250ms (simulated disconnection)")

    print("\n📦 Generating sample data...")
    video_data, sensor_data = generate_sample_data()

    print(f"\n📹 Video Data ({len(video_data)} frames):")
    for v in video_data[:5]:  
        print(f"  {v}")
    if len(video_data) > 5:
        print(f"  ... ({len(video_data) - 5} more frames)")

    print(f"\n📡 Sensor Data ({len(sensor_data)} readings):")
    for s in sensor_data[:5]:  
        print(f"  {s}")
    if len(sensor_data) > 5:
        print(f"  ... ({len(sensor_data) - 5} more readings)")

    print("\n🔧 Creating Temporal Aligner...")
    aligner = TemporalAligner(
        sensor_data=sensor_data,
        max_gap_threshold=50.0  
    )

    print("\n⚙️  Starting alignment process (using Binary Search)...")
    aligned_pairs = aligner.align(video_data, use_interpolation=True)

    stats = aligner.get_statistics()

    print_alignment_results(aligned_pairs, stats)

    print("\n" + "=" * 100)
    print("⏱️  TIME COMPLEXITY ANALYSIS:")
    print("=" * 100)
    print("  • Binary Search (find_nearest_neighbor): O(log n)")
    print("    - n = number of sensor readings")
    print("    - Finds nearest sensor reading for each video frame")
    print("  • Align Operation: O(m log n)")
    print("    - m = number of video frames")
    print("    - n = number of sensor readings")
    print("    - Binary search performed for each frame")
    print("  • Interpolation: O(1)")
    print("    - Constant time, just a mathematical calculation")
    print("  • Space Complexity: O(n + m)")
    print("    - Storing both data sources")
    print("\n💡 This approach is much more efficient than naive linear search (O(mn))")
    print("   by using binary search!")
    print("=" * 100)

if __name__ == "__main__":
    main()