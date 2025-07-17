# Gacha Reroll Automation

A Python-based automation tool for monitoring and detecting specific characters in gacha games using LDPlayer Android emulator instances.

## Features

- **Multi-Instance Monitoring**: Monitor multiple LDPlayer instances simultaneously
- **Smart Character Detection**: Uses AI-powered image recognition to detect target characters
- **Automated Screenshot Analysis**: Takes screenshots at configurable intervals and analyzes them
- **Duplicate Detection**: Automatically ignores instances that send duplicate screenshots
- **Auto-Instance Management**: Automatically close instances when they reach target goals
- **GUI Interface**: User-friendly interface with real-time monitoring and statistics
- **Configurable Timings**: Customizable screenshot timings and monitoring durations

## Requirements

- Python 3.7+
- LDPlayer Android emulator
- ADB (Android Debug Bridge)
- Windows OS (tested on Windows 10/11)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/gacha-reroll-automation.git
   cd gacha-reroll-automation
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3Configure LDPlayer**:
   - Install LDPlayer and create multiple instances
   - Enable ADB in LDPlayer settings
   - Note the ADB paths for your installation

4d character images**:
   - Place character images in the `characters/` folder
   - Images should be clear screenshots of the target character
   - Supported formats: PNG, JPG, JPEG, BMP

## Configuration

### Initial Setup

1. **ADB Configuration**:
   - Set the correct ADB path (usually `E:\LDPlayer\LDPlayer9\adb.exe`)
   - Set the LDPlayer console path (usually `E:\LDPlayer\LDPlayer9\ldconsole.exe`)

2. **Instance Setup**:
   - Use Auto Discover toautomatically find running LDPlayer instances
   - Or manually set the number of instances and generate ports

3. **Character Detection**:
   - Click "Initialize Detector" to set up smart character detection
   - The system will use all images from the `characters/` folder

### Default Settings

- **Monitoring Duration**: 3 minutes 53 seconds
- **Cycle Duration**: 4 seconds
- **Target Successful Pulls**: 4
- **Screenshot Timings**: 2:22, 2:35, 2:47, 3:0, 35, 3:27, 3:41
- **Deduplication Distance**: 150 pixels
- **Target Character**: Kita Black

## Usage

1. **Start the Application**:
   ```bash
   python simple_reroll_monitor.py
   ```

2. **Configure Settings**:
   - Set ADB paths
   - Configure instance count
   - Set target character name
   - Adjust screenshot timings as needed

3. **Initialize Detection**:
   - Click "Initialize Detector" to set up character recognition

4. **Start Monitoring**:
   - ClickStart Monitoring"
   - Press Page Down to trigger macros in LDPlayer
   - The system will automatically monitor and detect characters

## Features in Detail

### Smart Character Detection
- Uses multiple detection methods for higher accuracy
- Configurable confidence threshold (default: 85%)
- Deduplication to avoid counting the same character multiple times
- Supports multiple character images for better recognition

### Duplicate Screenshot Detection
- Automatically detects when an instance sends the same screenshot twice
- Ignores instances that are stuck or frozen
- Resets at the start of each new cycle

### Screenshot Management
- First cycle: Saves screenshots from first and last instances
- Subsequent cycles: Saves annotated screenshots when characters are detected
- Automatic cleanup of temporary files

### Instance Management
- Auto-discovery of LDPlayer instances
- Automatic closing of instances when they reach target goals
- Real-time status tracking for each instance

## File Structure

```
gacha-reroll-automation/
├── simple_reroll_monitor.py      # Main application
├── smart_character_detection.py  # Character detection engine
├── requirements.txt              # Python dependencies
├── config.ini                    # Configuration file
├── config_template.ini           # Configuration template
├── characters/                   # Character images folder
├── saved_images/                 # Saved screenshots folder
└── README.md                     # This file
```

## Configuration Files

### config.ini
Contains user-specific settings:
- ADB paths
- LDPlayer console path
- Other user preferences

### config_template.ini
Template file showing available configuration options.

## Troubleshooting

### Common Issues

1. **ADB Connection Failed**:
   - Ensure LDPlayer is running
   - Check if ADB is enabled in LDPlayer settings
   - Verify ADB path is correct
   - Try restarting LDPlayer

2*No Characters Detected**:
   - Check character images in `characters/` folder
   - Ensure images are clear and representative
   - Adjust confidence threshold if needed
   - Verify target character name matches3 **Screenshots Not Saving**:
   - Check folder permissions
   - Ensure `saved_images/` folder exists
   - Verify disk space

4nstances Not Found**:
   - Use "Auto Discover" feature
   - Check if instances are running
   - Verify ADB is enabled in LDPlayer

### Debug Tools

The application includes several debug tools:
- **Test ADB Connection**: Verify ADB connectivity
- **Debug ADB**: Detailed ADB troubleshooting
- **Test LDConsole**: Verify LDPlayer console functionality
- **Take Test Screenshot**: Test screenshot functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and personal use only. Please ensure you comply with the terms of service of any games you use this with. The authors are not responsible for any consequences of using this software.

## Support

If you encounter issues or have questions:
1. Check the troubleshooting section
2. Review the configuration
3. Open an issue on GitHub with detailed information 