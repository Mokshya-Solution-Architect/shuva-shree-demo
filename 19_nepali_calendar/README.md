# Nepali Calendar (Bikram Sambat) for Odoo 19

A comprehensive Odoo 19 module that integrates the Nepali Calendar (Bikram Sambat) system throughout the entire Odoo interface.

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Odoo](https://img.shields.io/badge/odoo-19.0-green.svg)
![License](https://img.shields.io/badge/license-LGPL--3-blue.svg)

## 📋 Description

This module adds full Nepali Calendar (Bikram Sambat - B.S) support to Odoo 19, allowing users to view and interact with dates in the Nepali calendar system alongside or instead of the Gregorian (A.D) calendar.

### Key Features

✨ **Multiple Display Formats**
- **B.S in English**: Display dates in Bikram Sambat with English numerals (e.g., `2081 Kartik 15`)
- **B.S in Nepali Unicode**: Display dates with Nepali Devanagari numerals (e.g., `२०८१ कार्तिक १५`)
- **B.S + A.D Combined**: Show both calendars together (e.g., `2081 Kartik 15 (2024-11-27)`)
- **A.D Only**: Keep standard Gregorian calendar format

📅 **Interactive Calendar Picker**
- Beautiful BS calendar with Nepali month names
- Toggle between BS and AD calendars when in combined mode
- Month and year dropdowns for quick navigation
- Visual indicators for today and selected dates
- Support for both Date and DateTime fields

🎯 **Universal Coverage**
- **Form Views**: All date/datetime fields show BS format
- **List Views**: Date columns display in BS format
- **Kanban Views**: Date cards show BS dates
- **Calendar Views**: Events display with BS dates
- **Pivot/Graph Views**: Date dimensions use BS format
- **Reports**: Optional BS date display in reports

⚙️ **Centralized Settings**
- Configure date format from Settings page
- Customizable date patterns (e.g., `YYYY MMMM DD`, `YYYY-MM-DD`)
- Separate configuration for date and datetime fields
- Settings apply system-wide automatically

🌐 **Date Range Support**
- Covers Bikram Sambat years **2000 to 2100** (A.D 1943-2044)
- Accurate conversion using official Nepali calendar data
- Handles variable month lengths correctly

## 📦 Installation

### Prerequisites
- Odoo 19.0
- Python 3.10 or higher
- Web browser with JavaScript enabled

### Installation Steps

#### Method 1: Using Odoo Apps

1. Download the module as a ZIP file
2. Extract to your Odoo addons directory:
   ```bash
   cd /opt/odoo19/custom-addons
   unzip 19_nepali_calendar.zip
   ```

3. Set proper permissions:
   ```bash
   sudo chown -R odoo:odoo /opt/odoo19/custom-addons/19_nepali_calendar
   sudo chmod -R 755 /opt/odoo19/custom-addons/19_nepali_calendar
   ```

4. Restart Odoo server:
   ```bash
   sudo systemctl restart odoo19
   ```

5. Update Apps List:
   - Go to **Apps** menu
   - Click **Update Apps List**
   - Search for "Nepali Calendar"
   - Click **Install**

#### Method 2: Command Line Installation

```bash
# Navigate to Odoo directory
cd /opt/odoo19/odoo

# Install the module
./odoo-bin -d your_database -i 19_nepali_calendar --stop-after-init

# Restart Odoo
sudo systemctl restart odoo19
```

#### Method 3: Git Clone

```bash
# Clone directly to addons directory
cd /opt/odoo19/custom-addons
git clone https://github.com/yourusername/19_nepali_calendar.git

# Restart and install
sudo systemctl restart odoo19
```

## 🚀 Configuration

### Initial Setup

1. **Access Settings**
   - Go to **Settings** (⚙️ icon in app menu)
   - Scroll to **Nepali Calendar** section

2. **Enable Feature**
   ```
   ☑ Enable Nepali Calendar Features
   ```

3. **Configure Date Format**

   Choose your preferred display format:

   **Option A: B.S in English**
   ```
   Date Display Format: ⦿ B.S in English
   Example: 2081 Kartik 15
   ```

   **Option B: B.S in Nepali Unicode**
   ```
   Date Display Format: ⦿ B.S in Nepali Unicode
   Example: २०८१ कार्तिक १५
   ```

   **Option C: B.S + A.D Combined**
   ```
   Date Display Format: ⦿ B.S + A.D Combined
   Example: 2081 Kartik 15 (2024-11-27)
   ```

   **Option D: A.D Only (Default)**
   ```
   Date Display Format: ⦿ A.D Only
   Example: 11/27/2024
   ```

4. **Configure Date Pattern**

   Choose how dates are formatted:
   ```
   Date Pattern: YYYY MMMM DD    → 2081 Kartik 15
   Date Pattern: YYYY-MM-DD      → 2081-08-15
   Date Pattern: DD MMMM YYYY    → 15 Kartik 2081
   Date Pattern: MMMM DD, YYYY   → Kartik 15, 2081
   ```

5. **Configure DateTime Format**

   Set datetime display format (can be different from date format):
   ```
   DateTime Display Format: ⦿ B.S in English
   DateTime Pattern: YYYY MMMM DD HH:mm
   Example: 2081 Kartik 15 14:30
   ```

6. **Configure Calendar Picker Mode**
   ```
   Calendar Picker Mode: ⦿ Both (B.S + A.D with toggle)
   Calendar Picker Mode: ⦿ B.S Calendar only
   Calendar Picker Mode: ⦿ A.D Calendar only
   ```

7. **Click Save**
   ```
   💾 Save
   ```

8. **Hard Refresh Browser** ⚠️ **CRITICAL STEP**

   After saving settings, you **MUST** refresh your browser to load the new configuration:

   **Windows/Linux**: `Ctrl + Shift + R`

   **Mac**: `Cmd + Shift + R`

### Configuration Examples

#### Example 1: Pure Nepali (Unicode)
```
☑ Enable Nepali Calendar Features
Date Display Format: ⦿ B.S in Nepali Unicode
Date Pattern: YYYY MMMM DD
DateTime Format: ⦿ B.S in Nepali Unicode
DateTime Pattern: YYYY MMMM DD HH:mm
Calendar Picker Mode: ⦿ B.S Calendar only

Result:
Form View: २०८१ कार्तिक १५
List View: २०८१ कार्तिक १५
Calendar Picker: Only BS calendar shown
```

#### Example 2: Bilingual (Best for Transition)
```
☑ Enable Nepali Calendar Features
Date Display Format: ⦿ B.S + A.D Combined
Date Pattern: YYYY-MM-DD
DateTime Format: ⦿ B.S + A.D Combined
DateTime Pattern: YYYY-MM-DD HH:mm
Calendar Picker Mode: ⦿ Both

Result:
Form View: 2081-08-15 (2024-11-27)
List View: 2081-08-15 (2024-11-27)
Calendar Picker: Toggle button to switch BS ↔ AD
```

#### Example 3: English BS (Clean & Professional)
```
☑ Enable Nepali Calendar Features
Date Display Format: ⦿ B.S in English
Date Pattern: YYYY MMMM DD
DateTime Format: ⦿ B.S in English
DateTime Pattern: YYYY MMMM DD HH:mm
Calendar Picker Mode: ⦿ Both

Result:
Form View: 2081 Kartik 15
List View: 2081 Kartik 15
Calendar Picker: Toggle available
```

## 📖 Usage

### Using the Calendar Picker

#### Opening the Picker
1. Click on any date or datetime field
2. Calendar picker opens automatically

#### BS Calendar Features
- **Month Selector**: Dropdown to select Nepali month (Baishakh to Chaitra)
- **Year Selector**: Dropdown to select BS year (2000-2100)
- **Navigation Buttons**: Previous/Next month arrows
- **Day Grid**: Click any date to select
- **Today Highlight**: Current BS date highlighted in yellow
- **Selected Date**: Chosen date highlighted in blue

#### Toggle Between BS and AD (Combined Mode)
1. When in "B.S + A.D Combined" or "Both" mode
2. Click the **calendar icon button** at the top
3. Calendar switches between BS and AD views
4. Selected date is preserved during toggle

#### Keyboard Navigation
- **Tab**: Move between month/year dropdowns
- **Arrow Keys**: Navigate in dropdowns
- **Enter**: Select date
- **Escape**: Close picker

### Working with Different Views

#### Form View
- Open any record (e.g., Employee, Sale Order)
- Date fields automatically display in configured BS format
- Click to open picker and select BS date
- Changes save as standard AD dates in database

#### List View
- Date columns automatically show BS format
- Click column header to sort by date (uses AD internally)
- Filter by dates using BS calendar picker
- Export to Excel maintains BS format

#### Kanban View
- Date cards display in BS format
- Drag and drop works normally
- Date-based grouping uses BS months

#### Calendar View
- Events show with BS dates
- Month/week/day views use BS calendar
- Create events using BS date picker
- All-day events respect BS dates

#### Pivot/Graph View
- Date dimensions use BS format
- Grouping by month uses Nepali months
- Charts display BS dates on axes
- Drill-down maintains BS format

### Date Filtering

When filtering records by date:

1. Click **Filters** button
2. Select date filter (e.g., "Join Date")
3. BS calendar picker opens
4. Select date range using BS calendar
5. Results filtered correctly

### Date Search

To search by date:

1. Use search bar
2. Type BS date in configured format
   - Example: `2081 Kartik`
3. Results show matching records

## 🎨 Customization

### Custom Date Patterns

You can create custom date patterns using these tokens:

| Token | Description | Example |
|-------|-------------|---------|
| `YYYY` | 4-digit year | 2081 |
| `YY` | 2-digit year | 81 |
| `MMMM` | Full month name | Kartik |
| `MMM` | Short month name | Kar |
| `MM` | 2-digit month | 08 |
| `M` | Month number | 8 |
| `DD` | 2-digit day | 15 |
| `D` | Day number | 15 |
| `HH` | 24-hour format | 14 |
| `hh` | 12-hour format | 02 |
| `mm` | Minutes | 30 |
| `ss` | Seconds | 45 |

**Examples:**
```
YYYY MMMM DD        → 2081 Kartik 15
YYYY-MM-DD          → 2081-08-15
DD/MM/YYYY          → 15/08/2081
MMMM DD, YYYY       → Kartik 15, 2081
DD MMM YY           → 15 Kar 81
YYYY-MM-DD HH:mm    → 2081-08-15 14:30
```

### Styling the Calendar

The calendar appearance can be customized by modifying:
- `static/src/scss/nepali_datepicker.scss`

Key CSS classes:
- `.nepali_calendar_container` - Main container
- `.nepali_calendar_header` - Month/year header
- `.nepali_calendar_days` - Day grid
- `.nepali_calendar_day.today` - Today's date
- `.nepali_calendar_day.selected` - Selected date

## 🔧 Technical Details

### Architecture

```
┌─────────────────────────────────────────┐
│         Settings (Backend)              │
│  - res.config.settings                  │
│  - ir.config_parameter                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Controller (Python)                │
│  - /nepali_calendar/get_settings        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│    JavaScript Service                   │
│  - nepali_calendar_service.js           │
│  - Caches settings                      │
└────────────────┬────────────────────────┘
                 │
         ┌───────┴───────┐
         ▼               ▼
┌─────────────────┐ ┌──────────────────┐
│  Date Formatter │ │  Calendar Picker │
│  (List Views)   │ │  (Form Views)    │
└─────────────────┘ └──────────────────┘
```

### File Structure

```
19_nepali_calendar/
├── __init__.py
├── __manifest__.py
├── README.md
│
├── models/
│   ├── __init__.py
│   └── res_config_settings.py          # Settings model
│
├── controllers/
│   ├── __init__.py
│   └── main.py                         # Settings endpoint
│
├── views/
│   └── res_config_settings_views.xml   # Settings UI
│
├── security/
│   └── ir.model.access.csv             # Access rights
│
├── static/src/
│   ├── js/
│   │   ├── nepali_date_converter.js    # BS ↔ AD conversion
│   │   ├── nepali_calendar_service.js  # Settings service
│   │   ├── nepali_date_field_settings.js         # Form view patches
│   │   ├── nepali_date_field_enhanced.js         # List view formatters
│   │   └── nepali_datepicker_settings.js         # Calendar picker
│   │
│   ├── xml/
│   │   └── nepali_datepicker.xml       # Calendar template
│   │
│   └── scss/
│       └── nepali_datepicker.scss      # Calendar styles
│
└── data/
    └── nepali_calendar_data.js         # BS month data (2000-2100)
```

### Date Conversion

The module includes accurate BS ↔ AD conversion for:
- **BS Years**: 2000 to 2100
- **AD Years**: 1943 to 2044
- **Timezone**: Automatically uses Nepal Time (GMT+5:45)

Conversion uses official Nepal Calendar Development Committee data.

**Important**: All date conversions automatically use Nepal timezone (Asia/Kathmandu, GMT+5:45), ensuring correct dates regardless of the user's browser timezone. This means users anywhere in the world will see the correct BS date based on what day it is in Nepal.

### Database Storage

**Important**: Dates are always stored in the database as **AD dates** (standard Odoo format). The module only changes the **display** format. This ensures:
- ✅ Compatibility with other modules
- ✅ Database integrity
- ✅ Standard Odoo operations work normally
- ✅ Reports and APIs return AD dates (unless configured otherwise)

## 🐛 Troubleshooting

### Settings Not Applying

**Problem**: Changed settings but dates still show in old format

**Solution**:
1. **Hard refresh browser** (Critical!)
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`
2. If still not working, clear browser cache completely
3. Close and reopen browser

### List Views Showing AD Only

**Problem**: Form views show BS but list views show AD

**Solution**:
1. Check console for errors (F12)
2. Look for: `[Nepali Calendar Enhanced] Settings loaded from backend`
3. If missing, try:
   ```javascript
   // In browser console
   await window.nepaliCalendarDebug.checkMode()
   ```
4. Hard refresh browser

### Calendar Picker Not Showing BS

**Problem**: Calendar picker shows AD calendar even when BS format selected

**Solution**:
1. Check **Calendar Picker Mode** setting
2. Must be "Both" or "B.S Calendar only"
3. If "A.D Calendar only", picker won't show BS
4. Save and hard refresh

### Unicode Not Displaying

**Problem**: Seeing boxes instead of Nepali numerals

**Solution**:
1. Ensure system has Devanagari font installed
2. Install "Noto Sans Devanagari" or "Kalimati" font
3. Restart browser
4. Check browser font settings

### Dates Out of Range

**Problem**: Seeing "Date out of range" error

**Solution**:
- Module supports BS 2000-2100 (AD 1943-2044)
- Dates outside this range cannot be converted
- Use AD format for historical dates before 1943
- Use AD format for future dates after 2044

## 🧪 Testing

### Debug Console Commands

Open browser console (F12) and use these commands:

```javascript
// Check current settings and status
await window.nepaliCalendarDebug.checkMode()

// Test date conversion
window.nepaliCalendarDebug.testConversion('2024-11-27')
// Output:
// AD Date: 2024-11-27
// BS Date: {year: 2081, month: 8, day: 15}
// Formatted (English): 2081 Kartik 15
// Formatted (Unicode): २०८१ कार्तिक १५

// Test formatters
window.nepaliCalendarDebug.testFormatter('2024-11-27')
// Output:
// Date formatter: 2081 Kartik 15
// DateTime formatter: 2081 Kartik 15 14:30

// Reload settings after change
await window.nepaliCalendarDebug.reloadSettings()
```

### Verification Checklist

After installation and configuration:

- [ ] Settings page shows Nepali Calendar section
- [ ] Can save settings without errors
- [ ] Hard refresh browser performed
- [ ] Console shows: "Settings loaded from backend"
- [ ] Form view dates show in BS format
- [ ] List view dates show in BS format
- [ ] Calendar picker opens with BS calendar
- [ ] Toggle button works (if combined mode)
- [ ] Date selection saves correctly
- [ ] Filtered records show correct dates

## 📝 Changelog

### Version 1.0.0 (Current)
- ✨ Initial release
- ✨ Support for Odoo 19.0
- ✨ Multiple date display formats
- ✨ Interactive BS calendar picker
- ✨ All views support (form, list, kanban, calendar, pivot, graph)
- ✨ Configurable date patterns
- ✨ BS + AD combined format with toggle
- ✨ Unicode Nepali numerals support
- ✨ Centralized settings management
- ✨ Date range BS 2000-2100 (AD 1943-2044)

## 🤝 Support

### Documentation
- [Installation Guide](README.md#installation)
- [Configuration Guide](README.md#configuration)
- [Troubleshooting](README.md#troubleshooting)
- [Quick Start Guide](QUICKSTART.md)
- [All Views Support](ALL_VIEWS_SUPPORT.md)
- [Settings Refresh Guide](SETTINGS_REFRESH_REQUIRED.md)

### Debug Files (For Developers)
- [Final Fix Summary](FINAL_FIX_SUMMARY.md)
- [List View Fix Details](LIST_VIEW_FIX_COMPLETE.md)
- [Service Access Fix](SERVICE_ACCESS_FIX.md)
- [Toggle Button Feature](TOGGLE_BUTTON_FEATURE.md)

### Getting Help

If you encounter issues:

1. Check [Troubleshooting](#troubleshooting) section
2. Use debug console commands
3. Check browser console for errors (F12)
4. Review documentation files
5. Create an issue on GitHub (if applicable)

## 👥 Authors

**Your Name/Organization**
- Website: [your-website.com]
- Email: [your-email@example.com]
- GitHub: [github.com/yourusername]

## 📄 License

This module is licensed under **LGPL-3**.

You are free to:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

Under the conditions:
- 📋 Disclose source
- 📋 License and copyright notice
- 📋 State changes
- 📋 Same license (for derivatives)

See [LICENSE](LICENSE) file for full details.

## 🙏 Acknowledgments

- Nepal Calendar Development Committee for official calendar data
- Odoo Community for framework and tools
- Contributors and testers

## 🌟 Features Roadmap

Future enhancements planned:

- [ ] BS fiscal year support
- [ ] Nepali date in reports (PDF)
- [ ] Dashboard widgets with BS dates
- [ ] BS date comparison operators
- [ ] Custom BS date fields
- [ ] Mobile app support
- [ ] Translation to Nepali language
- [ ] BS date in emails/notifications
- [ ] Integration with HR (Dashain bonus, leave calculations)
- [ ] Integration with Accounting (BS fiscal periods)

## 💡 Tips & Best Practices

### For New Installations

1. **Start with Combined Format**
   - Use "B.S + A.D Combined" initially
   - Helps users transition from AD to BS
   - Can switch to BS-only later

2. **Test Before Production**
   - Install in test database first
   - Verify all date fields work
   - Check reports and exports

3. **Train Users**
   - Show how to use calendar picker
   - Explain toggle button (if enabled)
   - Demonstrate date filtering

### For Organizations

1. **Standardize Settings**
   - Use same format across company
   - Document chosen date pattern
   - Apply to all databases

2. **Consider Your Audience**
   - Government/NGO: Use Unicode Nepali
   - International business: Use combined format
   - Domestic business: Use English BS

3. **Plan for Reports**
   - Check if BS dates needed in printed reports
   - Configure "Show in Reports" setting
   - Test invoice/quotation printouts

## 🔒 Security

- Module requires standard Odoo user authentication
- Settings require "Settings" access rights
- No external API calls (fully offline)
- No data sent outside your Odoo instance
- All date conversions happen locally

## ⚡ Performance

- Settings cached in browser for performance
- Date conversions optimized for speed
- No database queries for each date display
- Minimal JavaScript bundle size (~50KB)
- Works smoothly with thousands of records

## 🌍 Internationalization

Currently supports:
- **English**: Interface and month names (romanized)
- **Nepali**: Unicode numerals and month names (Devanagari)

The module is designed to support additional languages through Odoo's standard translation system.

## 📊 Compatibility

### Odoo Versions
- ✅ Odoo 19.0 (Current)
- ⚠️ Odoo 18.0 (May require modifications)
- ❌ Odoo 17.0 and below (Not supported)

### Browsers
- ✅ Chrome/Chromium (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ✅ Edge (Latest)
- ⚠️ Internet Explorer (Not recommended)

### Database
- ✅ PostgreSQL 12+
- ✅ PostgreSQL 13+
- ✅ PostgreSQL 14+

### Operating Systems
- ✅ Linux (Ubuntu, Debian, CentOS, etc.)
- ✅ Windows Server
- ✅ macOS
- ✅ Docker containers

## 🎓 Learning Resources

### Nepali Calendar System

- Bikram Sambat starts from 57 BC
- 12 months: Baishakh to Chaitra
- Month lengths: 29-32 days (variable)
- New Year: Baishakh 1 (mid-April)
- Official calendar of Nepal

### Month Names

| # | Nepali | English | Days |
|---|--------|---------|------|
| 1 | बैशाख | Baishakh | 30-31 |
| 2 | जेठ | Jestha | 31-32 |
| 3 | असार | Ashadh | 31-32 |
| 4 | श्रावण | Shrawan | 31-32 |
| 5 | भाद्र | Bhadra | 31-32 |
| 6 | आश्विन | Ashwin | 30-31 |
| 7 | कार्तिक | Kartik | 29-30 |
| 8 | मंसिर | Mangsir | 29-30 |
| 9 | पौष | Poush | 29-30 |
| 10 | माघ | Magh | 29-30 |
| 11 | फाल्गुन | Falgun | 29-30 |
| 12 | चैत्र | Chaitra | 30-31 |

---

**Made with ❤️ for the Nepali Community**

🇳🇵 नेपाली क्यालेन्डर मोड्युल - Nepali Calendar Module

*Helping Nepali businesses and organizations use their traditional calendar system in modern ERP software.*
