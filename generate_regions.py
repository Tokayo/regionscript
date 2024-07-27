from PIL import Image
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import deque

def load_bmp(file_path):
    """ Load and validate the .bmp file """
    try:
        img = Image.open(file_path)
        if img.size != (6144, 4096):
            raise ValueError(f"Image dimensions are {img.size}, but expected 6144x4096.")
        return img
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def flood_fill(img, start_x, start_y, color, visited):
    """ Perform flood fill algorithm to find all connected pixels of the same color """
    width, height = img.size
    pixels = img.load()
    queue = deque([(start_x, start_y)])
    region_points = []
    
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        if pixels[x, y] != color:
            continue
        
        visited.add((x, y))
        region_points.append((x, y))
        
        queue.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    
    return region_points

def find_color_regions(img):
    """ Identify regions based on color IDs using flood fill """
    width, height = img.size
    pixels = img.load()
    regions = {}
    visited = set()

    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if (x, y) not in visited:
                region_points = flood_fill(img, x, y, color, visited)
                if color not in regions:
                    regions[color] = []
                regions[color].append(region_points)

    return regions

def bounding_rect(points):
    """ Calculate the bounding rectangle for a set of points """
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    return min_x, min_y, max_x - min_x + 1, max_y - min_y + 1

def create_rects(regions):
    """ Translate pixel areas into rectangular regions """
    rects = {}
    for color, region_list in regions.items():
        rects[color] = []
        for points in region_list:
            # Use a simple algorithm to split the points into smaller rectangles
            rects[color].extend(split_into_rects(points))
    return rects

def split_into_rects(points):
    """ Split the given points into smaller rectangles """
    points = set(points)
    rects = []
    
    while points:
        point = points.pop()
        x0, y0 = point
        width = 1
        height = 1
        
        # Extend the rectangle to the right
        while (x0 + width, y0) in points:
            points.remove((x0 + width, y0))
            width += 1
            
        # Extend the rectangle downwards
        for y in range(y0 + 1, y0 + height + 1):
            for x in range(x0, x0 + width):
                if (x, y) not in points:
                    break
            else:
                for x in range(x0, x0 + width):
                    points.remove((x, y))
                height += 1
                continue
            break
        
        rects.append((x0, y0, width, height))
    
    return rects

def prettify_xml(elem):
    """ Return a pretty-printed XML string for the Element """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generate_xml(rects, output_file):
    """ Generate Regions.xml file """
    root = ET.Element("ServerRegions")
    facet = ET.SubElement(root, "Facet", name="The World")
    
    for idx, (color, rect_list) in enumerate(rects.items(), start=1):
        region_name = f"Region_{idx}"  # Placeholder name, customize as needed
        region = ET.SubElement(facet, "region", type="Default", name=region_name)
        ET.SubElement(region, "rune", name=region_name)
        for min_x, min_y, width, height in rect_list:
            ET.SubElement(region, "rect", x=str(min_x), y=str(min_y), width=str(width), height=str(height))

    # Convert to pretty XML
    pretty_xml = prettify_xml(root)
    with open(output_file, 'w') as f:
        f.write(pretty_xml)

def main(bmp_file, output_file):
    img = load_bmp(bmp_file)
    if img is None:
        return

    regions = find_color_regions(img)
    rects = create_rects(regions)
    generate_xml(rects, output_file)
    print(f"Regions.xml generated successfully at {output_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Regions.xml from a .bmp image.")
    parser.add_argument("bmp_file", help="Path to the .bmp file.")
    parser.add_argument("output_file", help="Path to the output Regions.xml file.")

    args = parser.parse_args()

    main(args.bmp_file, args.output_file)
