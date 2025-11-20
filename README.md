**# Automated-Synthetic-Data-Pipeline-for-Object-Detection
A Python-based automation system developed to overcome the ‘data labeling’ bottleneck in computer vision projects, producing labels with 100% accuracy (ground-truth). The training and validation of the YOLOv8 model was performed using synthetic data generated with Domain Randomization techniques.
**# Temporal Aligner - Video-Sensor Synchronization

A high-performance Python library for temporally aligning video frames with sensor data streams. This system efficiently synchronizes data from different sources with varying sampling rates and handles missing data through interpolation and quality assessment.

## Overview

The Temporal Aligner is designed to solve the common problem of synchronizing data from multiple sources with different temporal characteristics:
- **Video data**: Typically sampled at 30 FPS (one frame every ~33.33ms)
- **Sensor data**: Often sampled at higher rates (e.g., 100 Hz, one reading every 10ms)

The system uses binary search algorithms for efficient nearest-neighbor matching and provides intelligent interpolation for missing or misaligned data points.

## Features

- ⚡ **Efficient Binary Search**: O(log n) nearest neighbor lookup using Python's `bisect` module
- 🔗 **Smart Interpolation**: Linear interpolation for numeric values when data points fall between sensor readings
- 📊 **Quality Assessment**: Automatic classification of aligned data as VALID, CORRUPTED, or INTERPOLATED
- 📈 **Comprehensive Statistics**: Detailed metrics on alignment quality and data integrity
- 🎯 **Configurable Thresholds**: Customizable gap thresholds for detecting corrupted or missing data
- 🔄 **Flexible Data Types**: Supports both numeric and non-numeric sensor values

## Classes and Components

### `DataQuality` (Enum)
Represents the quality status of an aligned data pair:
- `VALID`: Data points are well-aligned within acceptable time difference
- `CORRUPTED`: Time gap exceeds threshold, indicating potential data loss
- `INTERPOLATED`: Value was calculated through interpolation

### `DataPoint` (Dataclass)
Represents a single data point from either video or sensor source:
- `timestamp`: Float value in milliseconds
- `value`: Any type of data (numeric or non-numeric)
- `source`: String identifier for the data source

### `AlignedPair` (Dataclass)
Represents a synchronized pair of video and sensor data:
- `video_timestamp`: Timestamp of the video frame
- `video_value`: Value from the video source
- `sensor_timestamp`: Timestamp of the aligned sensor reading
- `sensor_value`: Value from the sensor (may be interpolated)
- `time_difference`: Absolute time difference between video and sensor timestamps
- `quality`: DataQuality enum indicating alignment quality
- `interpolation_used`: Boolean flag indicating if interpolation was applied

### `TemporalAligner` (Class)
Main alignment engine that performs temporal synchronization.

#### Methods

**`__init__(sensor_data, max_gap_threshold=50.0)`**
- Initializes the aligner with sensor data
- Automatically sorts sensor data by timestamp
- Sets the maximum acceptable time gap threshold (in milliseconds)

**`find_nearest_neighbor(target_timestamp)`**
- Uses binary search to find the nearest sensor reading to a target timestamp
- Returns tuple: `(index, time_difference)`
- Time complexity: O(log n)

**`interpolate(timestamp, before_idx, after_idx)`**
- Performs linear interpolation for numeric values
- Falls back to nearest neighbor for non-numeric values
- Time complexity: O(1)

**`align(video_data, use_interpolation=True)`**
- Main alignment method that synchronizes video frames with sensor data
- Returns list of `AlignedPair` objects
- Time complexity: O(m log n) where m = video frames, n = sensor readings

**`get_statistics()`**
- Returns comprehensive statistics dictionary including:
  - Total, valid, corrupted, and interpolated alignment counts
  - Percentage breakdowns
  - Sensor data count and threshold settings

## Installation

No external dependencies required! The code uses only Python standard library:
- `bisect` - For binary search operations
- `dataclasses` - For structured data classes
- `enum` - For quality status enumeration
- `typing` - For type hints

Python 3.7+ is required (for dataclasses support).

## Usage

### Basic Example

```python
from main import TemporalAligner, DataPoint

# Prepare sensor data
sensor_data = [
    DataPoint(timestamp=105.0, value=5.5, source="sensor"),
    DataPoint(timestamp=115.0, value=6.0, source="sensor"),
    DataPoint(timestamp=125.0, value=6.5, source="sensor"),
    # ... more sensor readings
]

# Prepare video data
video_data = [
    DataPoint(timestamp=100.0, value="frame_1", source="video"),
    DataPoint(timestamp=133.33, value="frame_2", source="video"),
    DataPoint(timestamp=166.66, value="frame_3", source="video"),
    # ... more video frames
]

# Create aligner and perform alignment
aligner = TemporalAligner(
    sensor_data=sensor_data,
    max_gap_threshold=50.0  # 50ms threshold
)

aligned_pairs = aligner.align(video_data, use_interpolation=True)

# Get statistics
stats = aligner.get_statistics()
print(f"Valid alignments: {stats['valid_percentage']:.1f}%")
```

### Running the Demo

The included `main()` function demonstrates the system with sample data:

```bash
python main.py
```

This will:
1. Generate sample video (30 FPS) and sensor (100 Hz) data
2. Simulate a sensor disconnection (missing data between 200-250ms)
3. Perform alignment with interpolation
4. Display detailed results and statistics

## Algorithm Details

### Binary Search Approach

The system uses binary search (`bisect.bisect_left`) to efficiently find the nearest sensor reading for each video frame:

1. **Find insertion point**: Binary search locates where the video timestamp would be inserted in the sorted sensor timestamp array
2. **Check neighbors**: Examines both left and right neighbors to find the closest match
3. **Select best**: Chooses the neighbor with minimum time difference

### Interpolation Strategy

When a video frame falls between two sensor readings:
1. **Check gap size**: If the gap between sensor readings exceeds the threshold, mark as CORRUPTED
2. **Numeric interpolation**: For numeric values, performs linear interpolation:
   ```
   value = v1 + (v2 - v1) * (t - t1) / (t2 - t1)
   ```
3. **Non-numeric fallback**: For non-numeric values, selects the nearest neighbor

### Quality Classification

- **VALID**: Time difference ≤ threshold and no interpolation needed
- **INTERPOLATED**: Value calculated through interpolation within acceptable gap
- **CORRUPTED**: Time difference > threshold or gap between sensor readings > threshold

## Time Complexity

| Operation | Complexity | Description |
|-----------|-----------|-------------|
| `find_nearest_neighbor` | O(log n) | Binary search for nearest sensor reading |
| `interpolate` | O(1) | Constant time interpolation calculation |
| `align` | O(m log n) | Binary search for each video frame |
| Space | O(n + m) | Storage for both data sources |

Where:
- **m** = number of video frames
- **n** = number of sensor readings

This is significantly more efficient than naive linear search (O(mn)).

## Example Output

```
====================================================================================================
TEMPORAL ALIGNMENT RESULTS
====================================================================================================

📊 STATISTICS:
  • Total Alignments: 10
  • Valid: 7 (70.0%)
  • Corrupted: 1 (10.0%)
  • Interpolated: 2 (20.0%)
  • Sensor Data Count: 25
  • Max Gap Threshold: 50.0ms

📋 ALIGNED PAIRS:
----------------------------------------------------------------------------------------------------
Video (ms)   Video Value          Sensor (ms) Sensor Value     Diff (ms)   Quality         Interp
----------------------------------------------------------------------------------------------------
100.00       kamera_karesi_1      105.00      5.00             5.00        ✅ valid        -
133.33       kamera_karesi_2      133.33      5.75             0.00        🔗 interpolated ✓
...
```

## Use Cases

- **Autonomous Vehicles**: Synchronizing camera frames with IMU/GPS sensor data
- **Sports Analytics**: Aligning video footage with motion sensor data
- **Medical Imaging**: Synchronizing video with physiological sensor readings
- **Robotics**: Aligning camera streams with joint position sensors
- **Research**: Any application requiring temporal alignment of heterogeneous data streams

## Configuration

### `max_gap_threshold`
Controls the maximum acceptable time difference between video and sensor data:
- **Lower values** (e.g., 20ms): Stricter alignment, more CORRUPTED classifications
- **Higher values** (e.g., 100ms): More lenient, fewer CORRUPTED classifications
- **Default**: 50.0ms (suitable for 30 FPS video with 100 Hz sensors)

### `use_interpolation`
Enables/disables interpolation:
- **True**: Attempts to interpolate values when video frames fall between sensor readings
- **False**: Uses only nearest neighbor matching

## Limitations

- Sensor data must be sortable by timestamp
- Interpolation only works for numeric values
- Non-numeric values use nearest neighbor selection
- Assumes timestamps are in the same time unit (milliseconds)

## Future Enhancements

Potential improvements:
- Support for multiple interpolation methods (cubic, spline)
- Outlier detection and filtering
- Automatic threshold optimization
- Support for timezone-aware timestamps
- Parallel processing for large datasets

## License

This code is part of the Orbifold project.

## Author

Orbifold Align Engine Simulation

