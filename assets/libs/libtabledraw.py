# Tabledraw: Librariy made by Simon Kalmi Claesson

def prepANSI(string):
    ANSI_PREFIX = "\033["
    ANSI_SUFFIX = "m"
    def replace_ansi(match):
        ansi_code = match.group(1)
        color_code = ansi_code.lstrip(ANSI_PREFIX).rstrip(ANSI_SUFFIX)
        return f"%{color_code}%"
    import re
    pattern = re.compile(f"({re.escape(ANSI_PREFIX)}\d+{re.escape(ANSI_SUFFIX)})")
    replaced_string = re.sub(pattern, replace_ansi, string)
    return replaced_string

def handleANSI(string):
    ANSI_PREFIX = "\033["
    ANSI_SUFFIX = "m"
    def replace_ansi(match):
        color_code = match.group(1)
        space = " "*len("%"+str(color_code)+"%")
        _len = len( f"{ANSI_PREFIX}{color_code}{ANSI_SUFFIX}{space}" )
        return f"{ANSI_PREFIX}{color_code}{ANSI_SUFFIX}".center(_len)
    import re
    pattern = r"%(\d+)%"
    replaced_string = re.sub(pattern, replace_ansi, string)
    return replaced_string

def drawTable(data=dict()):
    # extract the headers from the dictionary keys
    headers = list(data.keys())
    num_columns = len(headers)

    # calculate the width of each column
    widths = []

    # iterate over each header to calculate the maximum width of that column
    for header in headers:
        # start by assuming the width is the length of the header string plus two padding spaces
        width = len(header) + 2
        # iterate over each value in the column to find the maximum width of that value
        for value in data[header]:
            # the width of each value is the length of the string plus two padding spaces
            value_width = len(str(value)) + 2
            # update the column width if the value width is greater
            width = max(width, value_width)
        # add the final column width to the list of widths
        widths.append(width)

    # calculate the width of the divider row
    divider_width = sum(widths) + len(widths) - 1

    # render the table
    print("╭" + "┬".join("─" * width for width in widths) + "╮")

    # render the header row
    if len(headers) > 0:
        header_row = "│"
        for header, width in zip(headers, widths):
            # center the header string in its column and add padding spaces on either side
            header_row += header.center(width) + "│"
        print(header_row)

    # render the divider row
    print("├" + "┼".join("-" * width for width in widths) + "┤")

    # render each value row
    if len(headers) > 0:
        for i in range(len(data[headers[0]])):
            value_row = "│"
            for header, width in zip(headers, widths):
                # center the value string in its column and add padding spaces on either side
                value_row += handleANSI( prepANSI(str(data[header][i])).center(width) + "│")
            print(value_row)

    # render the bottom of the table
    print("╰" + "┴".join("─" * width for width in widths) + "╯")
