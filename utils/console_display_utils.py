
def truncateOrPadStrToWidth(string, width):
    # Truncate the string value if it is longer than the width
    truncatedStr = ((string[:width-2] + '..') if len(string) > width else string)
    
    # Add trailing whitespace to the string value if it is shorter than the width
    paddedStr = truncatedStr + (' ' * (width - len(truncatedStr)) if len(truncatedStr) < width else '')
    
    return paddedStr