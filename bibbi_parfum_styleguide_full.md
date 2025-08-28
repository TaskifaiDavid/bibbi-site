# BIBBI Parfum Style Guide & UX Rules

## Visual Style Guide

### Typography
- **Primary Typeface:** The BIBBI Parfum site uses a clean, modern **sans-serif** typeface for both headings and body text, reflecting a contemporary luxury feel. All text appears crisp and easy to read, suggesting a high-quality font likely similar to a **geometric or neo-grotesque sans-serif** (e.g. Helvetica Neue or a custom font). The **brand wordmark** “BIBBI” itself is set in an all-caps sans-serif, bold and clean, reinforcing a minimalist, modern identity.  
- **Headings:** Site headings (e.g. product titles, section headers) are presented in **uppercase** for emphasis and brand consistency. For example, product names like **“SWIMMING POOL”** or **“THE OTHER ROOM”** appear in all caps on the site. Headings are sized generously for hierarchy – the main page title or product name (often an `<h1>`) is large (approximately *2–3rem*, ~32–48px) and bold. Subheadings (like the “Founder” section title or product category labels) are slightly smaller (around *1.5rem*, ~24px) and may use a medium weight. All headings have ample **letter-spacing** to enhance the uppercase presentation and add an airy, elegant feel.  
- **Body Text:** Paragraph and body content use the same sans-serif font in **sentence case** (mixed case) for readability. The font-weight is typically **normal/regular**, providing a comfortable reading experience. Body text is around **16px** (1rem) with a **line-height** of roughly *1.5* for legibility. For instance, the founder’s story and product descriptions are in a clear regular font, black on a light background, with sufficient line spacing. Longer blocks of text (e.g. the product story or founder bio) are broken into short paragraphs or even introduced in smaller subsection headings to avoid wall-of-text.  
- **Secondary/Text Styles:** Smaller UI text elements (like form labels, menu and button text) also follow the sans-serif font. Often these smaller texts are **uppercase** as well – for example, the **“BUY”** button label and navigation menu items are all caps, indicating a stylistic choice to unify text appearance. These may be slightly lighter weight or smaller size (14px–15px) but remain legible. The top notification bar (e.g. “Free shipping for orders above 100€…”) and category tags like **“UNISEX PERFUME”** on product pages appear in an all-caps *small font*, possibly with subtle letter-spacing, to serve as understated labels.  
- **Emphasis & Variations:** The site generally avoids italic or decorative fonts to maintain its clean aesthetic. Instead, emphasis is achieved through **uppercase text**, **bold weight** for important names or terms, or using a slightly different size. Quotes or special notes (such as the perfume “personality” or usage instructions) might be in all caps or separated by line breaks for differentiation. Overall, the typography communicates a **contemporary, luxe tone** – straightforward and elegant, with all-caps used strategically to echo the brand’s bold style.

### Color Palette
- **Signature Blue:** The hallmark of BIBBI’s visual identity is its **deep vivid blue** hue, inspired by “Klein Blue.” This **rich cobalt blue** is the primary brand color, used prominently in packaging and accents. It’s a **bold, saturated blue** (approximately **Hex `#002FA7`**, the classic International Klein Blue) that appears in elements like the perfume bottle caps and labels. The brand is *“characterised by an unforgettable, vivid deep blue aesthetic,”* making this color central to all designs.  
- **Neutral Backgrounds:** The site favors a **clean, light background** for a gallery-like look. Predominantly, backgrounds are **white** or a very **pale warm gray** (near-white, e.g. Hex `#EFEDEB`). This neutral canvas allows the vibrant blue and product imagery to pop. White (`#FFFFFF`) is used for most page backgrounds, while off-white is used sparingly to add subtle warmth.  
- **Text and Secondary Colors:** **Black** (`#000000`) is used for nearly all text for maximum readability. Occasionally, a **dark charcoal** (`#111111`) softens the effect. Secondary info may use a **medium gray** for less emphasis.  
- **Accent Colors:** Minimal use beyond the primary blue. White is used on blue backgrounds, and gray for dividers or secondary states. No extraneous accent colors are employed.

### Logo Usage Guidelines
- **Format:** Wordmark in all caps sans-serif. “BIBBI” sometimes with “PARFUM” beneath.  
- **Color:** Black, white, or brand blue depending on background. Avoid placing blue logo on blue background.  
- **Clear Space:** Minimum space equal to the height of the “B”.  
- **Do not:** Stretch, recolor outside palette, skew, or add effects.  
- **Placement:** Header (top-left/center), footer, or on white/blue backgrounds with proper contrast.

### Imagery and Photography Style
- **Tone & Mood:** Artistic, mystical, modern. Evocative product storytelling.  
- **Lighting:** Dramatic yet clean, with emphasis on the vivid blue.  
- **Composition:** Minimalist, centered products, plenty of negative space. Founder rarely shown; focus on products.  
- **Editing:** Consistent grading, true brand blue, crisp resolution, subtle contrast.  
- **Usage in Tools:** High-quality product images, minimal stock imagery, neutral/blue backgrounds.

### Layout Grid & Spacing
- **Grid System:** 12-column responsive grid. 3–4 columns desktop, 2 tablet, 1 mobile.  
- **Spacing:** Generous whitespace, ~16–24px gutters, consistent vertical rhythm (~8px multiples).  
- **Alignment:** Content centered or evenly aligned. Cards and titles line up across rows.  
- **Responsive:** Breakpoints at ~1200px, 1024px, 768px, 576px.  

### Component Styling
#### Buttons
- **Primary:** Filled with brand blue, uppercase white text, small radius (4px).  
- **Hover:** Slightly darker blue or subtle shadow.  
- **Secondary:** Outline/ghost with blue text.  
- **Size:** 14–16px font, padding 0.5rem x 1rem.

#### Form Inputs
- **Style:** Minimalist, thin gray border or underline. White background.  
- **Focus:** Border highlight in blue.  
- **Labels:** Small, subtle, above field.  
- **Errors:** Small red text message.  

#### Product Cards
- **Structure:** Image, name (caps), price, centered.  
- **Style:** No border, no heavy shadow. White background.  
- **Hover:** Swap image or zoom, underline name.  
- **Spacing:** Consistent margin/padding, grid-aligned.

#### Modals
- **Overlay:** Semi-transparent black/blue.  
- **Content:** White panel, small radius, subtle shadow.  
- **Typography:** Brand font, centered headings.  
- **Transitions:** Fade/slide, smooth easing.

#### Icons
- **Style:** Thin outline, 1.5–2px stroke.  
- **Color:** Black, white, or brand blue.  
- **Size:** ~20px, consistent stroke width.  
- **Consistency:** Uniform style set, no fills.

## UX Guidelines

### Navigation Patterns
- **Desktop:** Top header with logo, “All Products” (hover dropdown), search, login, cart icons. Sticky header.  
- **Mobile:** Hamburger menu, slide-in list. Cart/search icons remain top-right. Tap targets large enough.  

### Homepage Flow
1. **Hero:** Video/image, brand mood.  
2. **Product Grid:** Immediate product access.  
3. **Newsletter CTA:** “Join the BIBBI Universe”.  
4. **Founder Story:** Brand philosophy text.  
5. **Footer:** Links, newsletter, social icons.

### Product Page Flow
- Image gallery (multiple angles).  
- Title + category (caps).  
- Price/size selector, quantity.  
- CTA button (“BUY”).  
- Story/narrative (uppercase prose).  
- Notes breakdown (TOP, HEART, BASE).  
- Ingredients list (all caps).  
- Related products grid.  

### Interaction Patterns
- **Hover:** Subtle color shift, underline, or image swap.  
- **Scroll:** Smooth, lazy-load images. Sticky nav.  
- **Forms:** Inline validation, subtle blue highlight.  
- **Feedback:** Cart icon updates, confirmation text.  
- **Transitions:** Fade/slide, smooth 0.2–0.3s ease.

### Responsiveness & Mobile
- **Layout:** Collapse to single column.  
- **Touch:** Tap-friendly, 48px targets.  
- **Typography:** 16px+ body text, adjusted headings.  
- **Performance:** Optimized images, fast loads.  
- **Mobile-specific:** Hamburger menu, swipe galleries, simplified layout.

---
By following these UX rules and style guide details, the internal tool’s UI will **visually and experientially align with BIBBI Parfum’s site**, ensuring consistency in branding, typography, color, and interactions.
