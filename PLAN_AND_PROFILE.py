import arcpy
import os
import math

# === ModelBuilder Parameters ===
input_points = arcpy.GetParameterAsText(0)  # Input Point Feature Class
output_lines = arcpy.GetParameterAsText(1)  # Output Line Feature Class
input_length = float(arcpy.GetParameterAsText(4))  # Input Integer Length
row_number = int(arcpy.GetParameterAsText(5))  # Number of rows for grid
depth_polygons = arcpy.GetParameterAsText(3)  # Input Depth Polygons Feature Class
depth_type1 = arcpy.GetParameterAsText(6)  # Depth Type #1 String
depth_type2 = arcpy.GetParameterAsText(7)  # Depth Type #2 String
depth_dimension1 = int(arcpy.GetParameterAsText(8))  # Depth Dimension #1 Integer
depth_dimension2 = int(arcpy.GetParameterAsText(9))  # Depth Dimension #2 Integer
width_dimension1 = int(arcpy.GetParameterAsText(10))  # Width Dimension #1 Integer (East)
width_dimension2 = int(arcpy.GetParameterAsText(11))  # Width Dimension #2 Integer (West)
bore_line = arcpy.GetParameterAsText(2)  # Bore Line Feature Class
title = arcpy.GetParameterAsText(12)  # Title String

# === Derived value ===
half_length = input_length / 2.0

# === Spatial Reference ===
desc = arcpy.Describe(input_points)
spatial_ref = desc.spatialReference

def BoreLineGenerator(x, y, half_length, spatial_ref, insert_cursor):
    """Generate the main bore line from center point"""
    # Define direction (horizontal here)
    x1 = x - half_length
    x2 = x + half_length

    # Create original line (main line)
    p1 = arcpy.Point(x1, y)
    p2 = arcpy.Point(x, y)
    p3 = arcpy.Point(x2, y)

    array = arcpy.Array([p1, p2, p3])
    line = arcpy.Polyline(array, spatial_ref)
    insert_cursor.insertRow([line])
    
    return x1, x2

def GraphicLineGenerator(x, y, x1, x2, spatial_ref, insert_cursor):
    """Generate the extension lines using dynamic width dimensions"""
    # Use width dimensions for originalExtension - east (right) and west (left)
    originalExtension_east = width_dimension1  # Width dimension 1 for east/right side
    originalExtension_west = width_dimension2  # Width dimension 2 for west/left side
    
    # === Step 2: Create extensions from end points ===
    # Left extension (extending further left from x1) - uses west width dimension
    left_ext_start = arcpy.Point(x1 - originalExtension_west, y)
    left_ext_end = arcpy.Point(x1, y)
    left_ext_array = arcpy.Array([left_ext_start, left_ext_end])
    left_ext_line = arcpy.Polyline(left_ext_array, spatial_ref)
    insert_cursor.insertRow([left_ext_line])

    # Right extension (extending further right from x2) - uses east width dimension
    right_ext_start = arcpy.Point(x2, y)
    right_ext_end = arcpy.Point(x2 + originalExtension_east, y)
    right_ext_array = arcpy.Array([right_ext_start, right_ext_end])
    right_ext_line = arcpy.Polyline(right_ext_array, spatial_ref)
    insert_cursor.insertRow([right_ext_line])

    # === Step 3 & 4: Create 1ft extensions from the end points of original extensions ===
    # Left side 1ft extensions
    # From the far left end of the original extension
    left_1ft_start = arcpy.Point(x1 - originalExtension_west - 1, y)
    left_1ft_end = arcpy.Point(x1 - originalExtension_west, y)
    left_1ft_array = arcpy.Array([left_1ft_start, left_1ft_end])
    left_1ft_line = arcpy.Polyline(left_1ft_array, spatial_ref)
    insert_cursor.insertRow([left_1ft_line])

    # From the connection point between main line and left original extension
    left_conn_1ft_start = arcpy.Point(x1, y)
    left_conn_1ft_end = arcpy.Point(x1 + 1, y)
    left_conn_1ft_array = arcpy.Array([left_conn_1ft_start, left_conn_1ft_end])
    left_conn_1ft_line = arcpy.Polyline(left_conn_1ft_array, spatial_ref)
    insert_cursor.insertRow([left_conn_1ft_line])

    # Right side 1ft extensions
    # From the connection point between main line and right original extension
    right_conn_1ft_start = arcpy.Point(x2 - 1, y)
    right_conn_1ft_end = arcpy.Point(x2, y)
    right_conn_1ft_array = arcpy.Array([right_conn_1ft_start, right_conn_1ft_end])
    right_conn_1ft_line = arcpy.Polyline(right_conn_1ft_array, spatial_ref)
    insert_cursor.insertRow([right_conn_1ft_line])

    # From the far right end of the original extension
    right_1ft_start = arcpy.Point(x2 + originalExtension_east, y)
    right_1ft_end = arcpy.Point(x2 + originalExtension_east + 1, y)
    right_1ft_array = arcpy.Array([right_1ft_start, right_1ft_end])
    right_1ft_line = arcpy.Polyline(right_1ft_array, spatial_ref)
    insert_cursor.insertRow([right_1ft_line])

def RectangleMaker(x, y, x1, x2, spatial_ref, insert_cursor):
    """Generate rectangles stacked vertically along the combined dimension line based on row_number"""
    # Define the far extension lengths using width dimensions + 1ft
    farExtension_east = width_dimension1 + 1  # East side (right)
    farExtension_west = width_dimension2 + 1  # West side (left)
    
    # Create the combined dimension line (entire length including extensions)
    combined_start = arcpy.Point(x1 - farExtension_west, y)  # Far left (including extensions)
    combined_end = arcpy.Point(x2 + farExtension_east, y)    # Far right (including extensions)
    combined_array = arcpy.Array([combined_start, combined_end])
    combined_line = arcpy.Polyline(combined_array, spatial_ref)
    insert_cursor.insertRow([combined_line])
    
    # Calculate rows above and below to ensure even total
    if row_number % 2 == 0:
        # Even number - split evenly
        rows_above = row_number // 2
        rows_below = row_number // 2
    else:
        # Odd number - add extra row at bottom
        rows_above = row_number // 2
        rows_below = (row_number // 2) + 1
    
    # Create rectangles above the line (north) - stacked vertically
    for i in range(rows_above):
        bottom_y = y + i  # Each rectangle is 1ft higher than the previous
        top_y = bottom_y + 1
        
        # Bottom horizontal edge
        bottom_left = arcpy.Point(x1 - farExtension_west, bottom_y)
        bottom_right = arcpy.Point(x2 + farExtension_east, bottom_y)
        bottom_array = arcpy.Array([bottom_left, bottom_right])
        bottom_line = arcpy.Polyline(bottom_array, spatial_ref)
        insert_cursor.insertRow([bottom_line])
        
        # Top horizontal edge
        top_left = arcpy.Point(x1 - farExtension_west, top_y)
        top_right = arcpy.Point(x2 + farExtension_east, top_y)
        top_array = arcpy.Array([top_left, top_right])
        top_line = arcpy.Polyline(top_array, spatial_ref)
        insert_cursor.insertRow([top_line])
        
        # Left vertical edge
        left_vert_array = arcpy.Array([bottom_left, top_left])
        left_vert_line = arcpy.Polyline(left_vert_array, spatial_ref)
        insert_cursor.insertRow([left_vert_line])
        
        # Right vertical edge
        right_vert_array = arcpy.Array([bottom_right, top_right])
        right_vert_line = arcpy.Polyline(right_vert_array, spatial_ref)
        insert_cursor.insertRow([right_vert_line])
    
    # Create rectangles below the line (south) - stacked vertically downward
    for i in range(rows_below):
        top_y = y - i  # Each rectangle is 1ft lower than the previous
        bottom_y = top_y - 1
        
        # Top horizontal edge
        top_left = arcpy.Point(x1 - farExtension_west, top_y)
        top_right = arcpy.Point(x2 + farExtension_east, top_y)
        top_array = arcpy.Array([top_left, top_right])
        top_line = arcpy.Polyline(top_array, spatial_ref)
        insert_cursor.insertRow([top_line])
        
        # Bottom horizontal edge
        bottom_left = arcpy.Point(x1 - farExtension_west, bottom_y)
        bottom_right = arcpy.Point(x2 + farExtension_east, bottom_y)
        bottom_array = arcpy.Array([bottom_left, bottom_right])
        bottom_line = arcpy.Polyline(bottom_array, spatial_ref)
        insert_cursor.insertRow([bottom_line])
        
        # Left vertical edge
        left_vert_array = arcpy.Array([top_left, bottom_left])
        left_vert_line = arcpy.Polyline(left_vert_array, spatial_ref)
        insert_cursor.insertRow([left_vert_line])
        
        # Right vertical edge
        right_vert_array = arcpy.Array([top_right, bottom_right])
        right_vert_line = arcpy.Polyline(right_vert_array, spatial_ref)
        insert_cursor.insertRow([right_vert_line])

def AttributeManager():
    """Add Line_Type field and classify the original bore line geometry"""
    # Add the Line_Type text field to the output feature class
    arcpy.AddField_management(
        in_table=output_lines,
        field_name="Line_Type",
        field_type="TEXT",
        field_length=50
    )
    
    # Create a selection based on the input_length with +/-1ft margin of error
    min_length = input_length - 1
    max_length = input_length + 1
    
    # Build the selection expression
    selection_expression = f"Shape_Length >= {min_length} AND Shape_Length <= {max_length}"
    
    # Update only the features that match the criteria using UpdateCursor with where_clause
    with arcpy.da.UpdateCursor(output_lines, ["Line_Type"], where_clause=selection_expression) as update_cursor:
        for row in update_cursor:
            row[0] = "BORE_LINE"
            update_cursor.updateRow(row)
    
    arcpy.AddMessage(f"Line_Type field added and BORE_LINE features classified (length: {input_length} +/-1ft)")

def DepthGenerator():
    """Generate depth-related rectangles using polylines and add attributes"""
    # Add Depth_Type text field to the output lines feature class
    arcpy.AddField_management(
        in_table=output_lines,
        field_name="Depth_Type",
        field_type="TEXT",
        field_length=50
    )
    
    # Add PolyID integer field to the output lines feature class
    arcpy.AddField_management(
        in_table=output_lines,
        field_name="PolyID",
        field_type="LONG"
    )
    
    # Use width dimensions for originalExtension - east (right) and west (left)
    originalExtension_east = width_dimension1  # Width dimension 1 for east/right side (PolyID 2)
    originalExtension_west = width_dimension2  # Width dimension 2 for west/left side (PolyID 1)
    
    # Calculate the top row position based on row_number
    if row_number % 2 == 0:
        rows_above = row_number // 2
    else:
        rows_above = row_number // 2
    
    # Get the point coordinates from input_points
    with arcpy.da.SearchCursor(input_points, ["SHAPE@XY"]) as search_cursor:
        for row in search_cursor:
            x, y = row[0]
            
            # Calculate the top row Y position
            top_row_y = y + rows_above
            
            # Create polyline cursors for depth rectangles
            with arcpy.da.InsertCursor(output_lines, ["SHAPE@"]) as insert_cursor:
                
                # Create west depth rectangle (PolyID = 1, left of bore line)
                west_top_left = arcpy.Point(x - half_length - originalExtension_west, top_row_y)
                west_top_right = arcpy.Point(x - half_length, top_row_y)
                west_bottom_right = arcpy.Point(x - half_length, top_row_y - depth_dimension2)
                west_bottom_left = arcpy.Point(x - half_length - originalExtension_west, top_row_y - depth_dimension2)
                
                # Top horizontal edge (west)
                west_top_array = arcpy.Array([west_top_left, west_top_right])
                west_top_line = arcpy.Polyline(west_top_array, spatial_ref)
                insert_cursor.insertRow([west_top_line])
                
                # Bottom horizontal edge (west)
                west_bottom_array = arcpy.Array([west_bottom_left, west_bottom_right])
                west_bottom_line = arcpy.Polyline(west_bottom_array, spatial_ref)
                insert_cursor.insertRow([west_bottom_line])
                
                # Left vertical edge (west)
                west_left_array = arcpy.Array([west_top_left, west_bottom_left])
                west_left_line = arcpy.Polyline(west_left_array, spatial_ref)
                insert_cursor.insertRow([west_left_line])
                
                # Right vertical edge (west)
                west_right_array = arcpy.Array([west_top_right, west_bottom_right])
                west_right_line = arcpy.Polyline(west_right_array, spatial_ref)
                insert_cursor.insertRow([west_right_line])
                
                # Create east depth rectangle (PolyID = 2, right of bore line)
                east_top_left = arcpy.Point(x + half_length, top_row_y)
                east_top_right = arcpy.Point(x + half_length + originalExtension_east, top_row_y)
                east_bottom_right = arcpy.Point(x + half_length + originalExtension_east, top_row_y - depth_dimension1)
                east_bottom_left = arcpy.Point(x + half_length, top_row_y - depth_dimension1)
                
                # Top horizontal edge (east)
                east_top_array = arcpy.Array([east_top_left, east_top_right])
                east_top_line = arcpy.Polyline(east_top_array, spatial_ref)
                insert_cursor.insertRow([east_top_line])
                
                # Bottom horizontal edge (east)
                east_bottom_array = arcpy.Array([east_bottom_left, east_bottom_right])
                east_bottom_line = arcpy.Polyline(east_bottom_array, spatial_ref)
                insert_cursor.insertRow([east_bottom_line])
                
                # Left vertical edge (east)
                east_left_array = arcpy.Array([east_top_left, east_bottom_left])
                east_left_line = arcpy.Polyline(east_left_array, spatial_ref)
                insert_cursor.insertRow([east_left_line])
                
                # Right vertical edge (east)
                east_right_array = arcpy.Array([east_top_right, east_bottom_right])
                east_right_line = arcpy.Polyline(east_right_array, spatial_ref)
                insert_cursor.insertRow([east_right_line])
    
    # Update the depth rectangle lines with attributes using UpdateCursor
    # We'll identify depth lines by their Y coordinates and position relative to the bore line
    with arcpy.da.UpdateCursor(output_lines, ["SHAPE@", "Depth_Type", "PolyID"]) as update_cursor:
        for row in update_cursor:
            if row[1] is None and row[2] is None:  # Only update lines without existing attributes
                line_geom = row[0]
                first_point = line_geom.firstPoint
                last_point = line_geom.lastPoint
                
                # Check if this is a depth rectangle line by examining Y coordinates
                if first_point.Y != y:  # Not on the main bore line level
                    # Determine if it's west (left) or east (right) of center
                    line_center_x = (first_point.X + last_point.X) / 2
                    
                    if line_center_x < x:  # West side
                        row[1] = depth_type2
                        row[2] = 1
                    elif line_center_x > x:  # East side
                        row[1] = depth_type1
                        row[2] = 2
                    
                    update_cursor.updateRow(row)

def PolygonConnector():
    """Connect corner polylines from groups 1 and 2 to create polygons in depth_polygons feature class"""
    # Create the depth polygons feature class
    arcpy.CreateFeatureclass_management(
        out_path=os.path.dirname(depth_polygons),
        out_name=os.path.basename(depth_polygons),
        geometry_type="POLYGON",
        spatial_reference=spatial_ref
    )
    
    # Add Depth_Type text field to the depth polygons feature class
    arcpy.AddField_management(
        in_table=depth_polygons,
        field_name="Depth_Type",
        field_type="TEXT",
        field_length=50
    )
    
    # Add PolyID integer field to the depth polygons feature class
    arcpy.AddField_management(
        in_table=depth_polygons,
        field_name="PolyID",
        field_type="LONG"
    )
    
    # Add Title text field to the depth polygons feature class
    arcpy.AddField_management(
        in_table=depth_polygons,
        field_name="Title",
        field_type="TEXT",
        field_length=100
    )
    
    # Use width dimensions for originalExtension - east (right) and west (left)
    originalExtension_east = width_dimension1  # Width dimension 1 for east/right side (PolyID 2)
    originalExtension_west = width_dimension2  # Width dimension 2 for west/left side (PolyID 1)
    
    # Calculate the top row position based on row_number
    if row_number % 2 == 0:
        rows_above = row_number // 2
    else:
        rows_above = row_number // 2
    
    # Get the point coordinates from input_points
    with arcpy.da.SearchCursor(input_points, ["SHAPE@XY"]) as search_cursor:
        for row in search_cursor:
            x, y = row[0]
            
            # Calculate the top row Y position
            top_row_y = y + rows_above
            
            # Create polygon cursors for depth polygons
            with arcpy.da.InsertCursor(depth_polygons, ["SHAPE@", "Depth_Type", "PolyID", "Title"]) as insert_cursor:
                
                # Create west depth polygon (PolyID = 1, left of bore line)
                west_top_left = arcpy.Point(x - half_length - originalExtension_west, top_row_y)
                west_top_right = arcpy.Point(x - half_length, top_row_y)
                west_bottom_right = arcpy.Point(x - half_length, top_row_y - depth_dimension2)
                west_bottom_left = arcpy.Point(x - half_length - originalExtension_west, top_row_y - depth_dimension2)
                
                # Create west polygon array (clockwise order)
                west_array = arcpy.Array([west_top_left, west_top_right, west_bottom_right, west_bottom_left, west_top_left])
                west_polygon = arcpy.Polygon(west_array, spatial_ref)
                insert_cursor.insertRow([west_polygon, depth_type2, 1, None])
                
                # Create east depth polygon (PolyID = 2, right of bore line)
                east_top_left = arcpy.Point(x + half_length, top_row_y)
                east_top_right = arcpy.Point(x + half_length + originalExtension_east, top_row_y)
                east_bottom_right = arcpy.Point(x + half_length + originalExtension_east, top_row_y - depth_dimension1)
                east_bottom_left = arcpy.Point(x + half_length, top_row_y - depth_dimension1)
                
                # Create east polygon array (clockwise order)
                east_array = arcpy.Array([east_top_left, east_top_right, east_bottom_right, east_bottom_left, east_top_left])
                east_polygon = arcpy.Polygon(east_array, spatial_ref)
                insert_cursor.insertRow([east_polygon, depth_type1, 2, None])
                
                # Create background polygon (pink area) - covers the entire grid area
                # Calculate x1 and x2 from the center point
                x1 = x - half_length
                x2 = x + half_length
                
                # Calculate the full extent of the background polygon
                farExtension_east = width_dimension1 + 1  # East side (right)
                farExtension_west = width_dimension2 + 1  # West side (left)
                
                # Calculate rows above and below for full height
                if row_number % 2 == 0:
                    rows_above_bg = row_number // 2
                    rows_below_bg = row_number // 2
                else:
                    rows_above_bg = row_number // 2
                    rows_below_bg = (row_number // 2) + 1
                
                # Background polygon corners
                bg_top_left = arcpy.Point(x1 - farExtension_west, y + rows_above_bg)
                bg_top_right = arcpy.Point(x2 + farExtension_east, y + rows_above_bg)
                bg_bottom_right = arcpy.Point(x2 + farExtension_east, y - rows_below_bg)
                bg_bottom_left = arcpy.Point(x1 - farExtension_west, y - rows_below_bg)
                
                # Create background polygon array (clockwise order)
                bg_array = arcpy.Array([bg_top_left, bg_top_right, bg_bottom_right, bg_bottom_left, bg_top_left])
                bg_polygon = arcpy.Polygon(bg_array, spatial_ref)
                insert_cursor.insertRow([bg_polygon, "BACKGROUND", 0, title])

def BoreConnector():
    """Create a line connecting the bottom right corner of polygon 1 to the bottom left corner of polygon 2"""
    # Create the bore line feature class
    arcpy.CreateFeatureclass_management(
        out_path=os.path.dirname(bore_line),
        out_name=os.path.basename(bore_line),
        geometry_type="POLYLINE",
        spatial_reference=spatial_ref
    )
    
    # Add Line_Type text field to the bore line feature class
    arcpy.AddField_management(
        in_table=bore_line,
        field_name="Line_Type",
        field_type="TEXT",
        field_length=50
    )
    
    # Use width dimensions for originalExtension - east (right) and west (left)
    originalExtension_east = width_dimension1  # Width dimension 1 for east/right side (PolyID 2)
    originalExtension_west = width_dimension2  # Width dimension 2 for west/left side (PolyID 1)
    
    # Calculate the top row position based on row_number
    if row_number % 2 == 0:
        rows_above = row_number // 2
    else:
        rows_above = row_number // 2
    
    # Get the point coordinates from input_points
    with arcpy.da.SearchCursor(input_points, ["SHAPE@XY"]) as search_cursor:
        for row in search_cursor:
            x, y = row[0]
            
            # Calculate the top row Y position
            top_row_y = y + rows_above
            
            # Calculate polygon corner coordinates
            # West polygon (PolyID = 1) - bottom right corner
            west_bottom_right = arcpy.Point(x - half_length, top_row_y - depth_dimension2)
            
            # East polygon (PolyID = 2) - bottom left corner
            east_bottom_left = arcpy.Point(x + half_length, top_row_y - depth_dimension1)
            
            # Create the connecting line from west polygon bottom right to east polygon bottom left
            with arcpy.da.InsertCursor(bore_line, ["SHAPE@", "Line_Type"]) as insert_cursor:
                connect_array = arcpy.Array([west_bottom_right, east_bottom_left])
                connect_line = arcpy.Polyline(connect_array, spatial_ref)
                insert_cursor.insertRow([connect_line, "BORE_CONNECTION"])

def CleanupTempGeometry():
    """Delete temporary dimension geometries created in DepthGenerator from output_lines"""
    try:
        # Build SQL query to select geometries with Shape_Length matching dimension parameters (+/- 1)
        # Check for depth_dimension1, depth_dimension2, width_dimension1, and width_dimension2
        
        conditions = []
        
        # Add condition for depth_dimension1 (+/- 1)
        conditions.append(f"(Shape_Length >= {depth_dimension1 - 1} AND Shape_Length <= {depth_dimension1 + 1})")
        
        # Add condition for depth_dimension2 (+/- 1)
        conditions.append(f"(Shape_Length >= {depth_dimension2 - 1} AND Shape_Length <= {depth_dimension2 + 1})")
        
        # Add condition for width_dimension1 (+/- 1)
        conditions.append(f"(Shape_Length >= {width_dimension1 - 1} AND Shape_Length <= {width_dimension1 + 1})")
        
        # Add condition for width_dimension2 (+/- 1)
        conditions.append(f"(Shape_Length >= {width_dimension2 - 1} AND Shape_Length <= {width_dimension2 + 1})")
        
        # Combine all conditions with OR to match any of the dimension lengths
        deleteSQL = " OR ".join(conditions)
        
        # Delete geometries that match the dimension lengths using UpdateCursor
        with arcpy.da.UpdateCursor(output_lines, ["Shape_Length"], where_clause=deleteSQL) as update_cursor:
            deleted_count = 0
            for row in update_cursor:
                update_cursor.deleteRow()
                deleted_count += 1
        
        arcpy.AddMessage(f"Temporary depth geometry cleaned up from output_lines - {deleted_count} features deleted")
        
    except Exception as e:
        arcpy.AddWarning(f"Could not clean up temporary geometry: {str(e)}")

def AddToMap():
    """Add the specified feature classes to the current map"""
    try:
        # Get the current project and active map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = aprx.activeMap
        
        # List of feature classes to add to map (parameters 0, 1, 4, and 11)
        feature_classes = [
            ("Profile Points", input_points),      # Parameter 0
            ("Output Lines", output_lines),        # Parameter 1 
            ("Depth Polygons", depth_polygons),    # Parameter 4
            ("Bore Line", bore_line)               # Parameter 11
        ]
        
        # Add each feature class to the map
        for layer_name, fc_path in feature_classes:
            if arcpy.Exists(fc_path):
                map_obj.addDataFromPath(fc_path)
                arcpy.AddMessage(f"Added {layer_name} to map")
            else:
                arcpy.AddWarning(f"Feature class {fc_path} does not exist and cannot be added to map")
                
    except Exception as e:
        arcpy.AddWarning(f"Could not add feature classes to map: {str(e)}")

def main():
    """Main function to orchestrate the line generation process"""
    # === Validate input points count ===
    point_count = int(arcpy.GetCount_management(input_points).getOutput(0))
    if point_count != 1:
        arcpy.AddError("Please use only one point in the Profile Point feature class.")
        return
    
    # === Create output feature class ===
    arcpy.CreateFeatureclass_management(
        out_path=os.path.dirname(output_lines),
        out_name=os.path.basename(output_lines),
        geometry_type="POLYLINE",
        spatial_reference=spatial_ref
    )

    # === Create lines from points ===
    with arcpy.da.SearchCursor(input_points, ["SHAPE@XY"]) as search_cursor, \
         arcpy.da.InsertCursor(output_lines, ["SHAPE@"]) as insert_cursor:

        for row in search_cursor:
            x, y = row[0]

            # Generate the main bore line and get end points
            x1, x2 = BoreLineGenerator(x, y, half_length, spatial_ref, insert_cursor)
            
            # Generate the graphic extension lines
            GraphicLineGenerator(x, y, x1, x2, spatial_ref, insert_cursor)
            
            # Generate the rectangles above and below the combined line
            RectangleMaker(x, y, x1, x2, spatial_ref, insert_cursor)

    # Add Line_Type field and classify the original bore line
    AttributeManager()
    
    # Generate depth rectangles using polylines
    DepthGenerator()
    
    # Create depth polygons by connecting corner polylines
    PolygonConnector()
    
    # Create bore connection line between polygons
    BoreConnector()
    
    # Clean up temporary dimension geometries
    CleanupTempGeometry()
    
    # Add feature classes to the map
    AddToMap()

    arcpy.SetParameter(1, output_lines)
    arcpy.AddMessage("Line generation complete.")

# Execute the main function
if __name__ == "__main__":
    main()