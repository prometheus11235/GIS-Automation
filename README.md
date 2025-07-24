# 📐 PLAN_AND_PROFILE.py – ArcGIS Pro Bore Profile Line Generator

🚀 **Automated spatial construction tool for bore lines, extensions, dimension rectangles, and depth polygons from a single point.**  
Designed for use in ArcGIS Pro with ModelBuilder integration.

---

## ✨ Features

- 📍 **Input-Driven Geometry Creation**  
  Generate horizontal bore lines and symmetrical extensions from a center point.

- 📏 **Dynamic Dimensioning**  
  Automatically creates:
  - 10-ft and 1-ft extension lines
  - Vertically stacked rectangles above/below the bore line
  - Depth rectangles with variable east/west dimensions

- 🧠 **Smart Attribute Assignment**  
  Classifies features like `BORE_LINE`, `Depth_Type`, and `PolyID` with embedded logic.

- 🧱 **Polygon Construction**  
  Builds full polygonal depth zones and background layers for advanced profile mapping.

- 🧹 **Cleanup Module**  
  Removes temporary lines based on dimension thresholds to keep your output tidy.

- 🗺️ **Auto Layer Injection**  
  Injects final geometries into your current ArcGIS Pro map project.

---

## 🧪 Parameters (via ModelBuilder)

| Parameter | Description |
|----------|-------------|
| `input_points` | Single-point feature class (origin) |
| `output_lines` | Output polyline feature class |
| `bore_line` | Connecting line between depth zones |
| `depth_polygons` | Output polygon feature class for depth rectangles |
| `input_length` | Horizontal bore length |
| `row_number` | Number of vertical rectangles (rows) |
| `depth_type1`/`2` | Text labels for east/west depth zones |
| `depth_dimension1`/`2` | Depths for east/west rectangles |
| `width_dimension1`/`2` | Widths for east/west extensions |
| `title` | Background polygon label |

---

## ⚙️ Workflow

```text
Input Point → Bore Line → Extensions → Dimension Rectangles
→ Depth Rectangles → Polygons → Bore Connector → Cleanup → Map
```

---

## 🛠️ Dependencies

- `arcpy` (ArcGIS Pro Python)
- ArcGIS Pro Project (`CURRENT` context for adding layers)

---

## 📌 Notes

- Expects **exactly one input point**.
- Outputs geometries in the spatial reference of the input point.
- Designed for integration into **ArcGIS ModelBuilder workflows** or as a standalone script tool.
