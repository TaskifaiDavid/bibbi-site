I checked your CSS and found the reason why the input box refuses to get wider: you have **multiple `max-width` constraints** applied in different selectors. For example:  

- `.input-container` → `max-width: 400px;`:contentReference[oaicite:0]{index=0}  
- `.chat-input-container` → `max-width: 900px;`:contentReference[oaicite:1]{index=1}  
- `.input-wrapper` → sometimes `max-width: none`, sometimes restricted:contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}  

Because CSS cascades, the **last loaded style and highest-specificity rule wins**. That’s why no matter what you change in one place, another selector is still limiting the width.  

---

### ✅ Fix
In your case, the input at the bottom of the screenshot is controlled by `.input-container` and `.chat-input-container`. To make it truly flexible, add this at the **end of your `index.css`**:

```css
.input-container,
.chat-input-container,
.input-wrapper {
  max-width: none !important;
  width: 100% !important;
}



