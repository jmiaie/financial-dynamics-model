# Logo Setup Guide

The Financial Dynamics Model Streamlit app includes support for displaying the Micap.AI logo in the sidebar.

## Current Setup

By default, the app includes a built-in **SVG logo** (`assets/micap_logo.svg`) that displays automatically when the app loads.

## Customizing with Your Own Logo

To use your custom Micap.AI logo instead of the default SVG:

### Option 1: PNG Logo (Recommended)

1. **Obtain your logo** in PNG format
2. **Save it as:** `assets/micap_logo.png`
3. **Restart the Streamlit app:** `streamlit run app.py`

The app will automatically detect and use the PNG logo instead of the SVG.

### Option 2: Keep the SVG Logo

The included SVG logo (`assets/micap_logo.svg`) works out of the box and is tracked in git, so it will be available across all deployments.

### Option 3: Use a Different Image Format

To add a custom logo in JPG, JPEG, or other formats:

1. Convert your image to PNG format (use an online converter or image editor)
2. Save it as `assets/micap_logo.png`
3. Restart the app

## Logo Display

- The logo appears in the bottom-left corner of the Streamlit sidebar
- It is clickable and links to https://micap.ai
- The logo respects the app's dark theme styling

## Technical Details

The app uses the `_get_logo_html()` function to:
1. Check for `assets/micap_logo.svg` first (always tracked in git)
2. Fall back to `assets/micap_logo.png` if available
3. Display the logo as inline SVG or base64-encoded PNG in the sidebar

The SVG logo is created with the app's color scheme:
- Dark slate background (`#0f172a`)
- Teal accents (`#0d7377`)
- Light teal highlights (`#14919b`)
- Green trend indicator (`#10b981`)

## File Size Considerations

- **SVG:** ~1 KB (vector-based, infinitely scalable)
- **PNG:** Varies (typically 10-50 KB for a logo)

For best performance, keep PNG logos under 100 KB.
