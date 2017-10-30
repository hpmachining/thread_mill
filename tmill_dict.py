#!python3
import math
import os


def get_thread_info():
    """
    Get and return the specifications for the thread to be milled.

    Prompts for the needed specifications for the thread to be milled
    and returns a dictionary of floats containing the information if the
    input is valid.

    Args:
        None.
    Returns:
        A dictionary of floats containing the thread specifications
        using the following keys:
        "Major diameter"
        "Minor diameter"
        "Thread depth"
        "Starting plane"
        "Pitch in threads per inch"
    Raises:
        ValueError: If input is not representable as a float or if any
        values other than the starting plane are <= 0.
    """

    threads = {
        "Major diameter": input("Major diameter:\n"),
        "Minor diameter": input("Minor diameter:\n"),
        "Thread depth": input("Thread depth:\n"),
        "Starting plane": input("Starting plane:\n"),
        "Threads per inch": input("Threads per inch:\n")
    }
    try:
        for key, value in threads.items():
            if key != "Starting plane" and float(value) <= 0.0:
                raise ValueError(key + " must be > 0.0")
            threads[key] = float(value)
        if threads["Minor diameter"] > threads["Major diameter"]:
            raise ValueError("Minor diameter must be less than Major diameter")
    except ValueError:
        raise
    return threads


def get_pass_percentages(passes):
    """
    Return a list of percentages to be used for radial depth of cut.

    Prompts for the number of passes and return a list of floats to
    be used as percentages of the depth of cut based on the number of
    passes. Valid inputs are 1, 2, 3, or 4.

    Args:
        None.
    Returns:
        A list containing the percentages to use for the radial
        depth of cuts based on the number of passes:
        1 pass = [1.0] (100%)
        2 passes = [.65, .35] (65%, 35%)
        3 passes = [.50, .30, .20] (50%, 30%, 20%)
        4 passes = [.40, .27, .20, .13] (40%, 27%, 20%, 13%)
    Raises:
        ValueError: If input is not representable as int or if input
        value is not 1, 2, 3 or 4
    """

    try:
        if not (0 < int(passes) < 5):
            raise ValueError(passes + " is not a valid option for number of passes")
    except ValueError:
        raise
    if int(passes) == 1:
        return [1.0]
    elif int(passes) == 2:
        return [.65, .35]
    elif int(passes) == 3:
        return [.50, .30, .20]
    else:
        return [.40, .27, .20, .13]


def get_tool_info():
    """
    Return a dictionary containing the specifications for the tool to be used.

    Prompts for the needed specifications for the thread mill tool
    to be used and returns a dictionary of floats containing the information
    if the input is valid.

    Args:
        None.
    Returns:
        A dictionary of floats containing the thread specifications
        using the following keys:
        "Tool diameter"
        "Number of flutes"
        "Speed" - Given in surface feet per minute (SFM)
        "Feed" - Given in feed per tooth"
    Raises:
        ValueError: If input is not representable as a float or value <= 0.
    """

    tool = {
        "Tool diameter": input("Tool diameter:\n"),
        "Number of flutes": input("Number of flutes:\n"),
        "Speed": input("Speed in surface feet per minute (SFM):\n"),
        "Feed": input("Feed per tooth:\n")
    }
    try:
        for key, value in tool.items():
            if float(value) <= 0.0:
                raise ValueError(key + " must be > 0.0")
            else:
                tool[key] = float(value)
    except ValueError:
        raise
    return tool


def get_toolpath_radii(thread, passes, tool_diameter):
    pass_count = len(passes)
    radii = []
    total_stock = round((thread["Major diameter"] - thread["Minor diameter"]) / 2.0, 5)
    base_radius = round((thread["Minor diameter"] - tool_diameter) / 2.0, 5)
    previous_radius = 0.0
    for i in passes:
        current_radius = round(base_radius + total_stock * i + previous_radius, 4)
        radii.append(current_radius)
        previous_radius = current_radius - base_radius
    return radii


def get_lead_radii(radii):
    sin_45 = math.sin(math.radians(45))
    return map(lambda lead: round(lead * sin_45, 4), radii)


def get_feed_adjustment(radii, tool_diameter):
    return map(lambda adjust: (adjust * 2.0)
                              / (adjust * 2.0 + tool_diameter), radii)


def write_begin(file_out, speed):
    file_out.write("S" + str(speed) + " M3" + "\n")
    file_out.write("\n")


def write_body(file_out,
               lead_arc,
               feed,
               feed_adjust,
               fast_feed,
               top_plane,
               start_z,
               radius,
               lead_z,
               pitch):
    start_x = round(lead_arc * math.sin(math.radians(45)), 4)
    start_y = -start_x
    adjusted_feed = round(feed * feed_adjust, 2)
    file_out.write("G90 G0 Z" + str(top_plane) + "\n")
    file_out.write("G91 G01 Z" + str(start_z)
                   + " F" + str(fast_feed)
                   + "\n")
    file_out.write("G01 X" + str(start_x)
                   + " Y" + str(start_y)
                   + " F" + str(adjusted_feed)
                   + "\n")
    file_out.write("G03 X" + str(round(radius - start_x, 4))
                   + " Y" + str(-start_y)
                   + " Z" + str(lead_z)
                   + " I0.0"
                   + " J" + str(-start_y)
                   + " F" + str(adjusted_feed)
                   + "\n")
    file_out.write("G03 X0.0 Y0.0 Z" + str(round(pitch, 4))
                   + " I" + str(round(-radius, 4))
                   + " J0.0"
                   + " F" + str(adjusted_feed)
                   + "\n")
    file_out.write("G03 X" + str(-start_x)
                   + " Y" + str(-start_y)
                   + " Z" + str(lead_z)
                   + " I" + str(-start_x)
                   + " J0.0"
                   + " F" + str(adjusted_feed)
                   + "\n")
    file_out.write("G01 X" + str(-start_x)
                   + " Y" + str(start_y)
                   + " F" + str(fast_feed)
                   + "\n")
    file_out.write("\n")


def write_end(file_out):
    file_out.write("M99\n")
    file_out.write("%\n")


def write_config_file(file_out,
                      file_name,
                      thread,
                      tool,
                      number_of_passes,
                      finish_passes):
    file_out.write(file_name + "\n")
    file_out.write(str(thread["Major diameter"]) + "\n")
    file_out.write(str(thread["Minor diameter"]) + "\n")
    file_out.write(str(thread["Thread depth"]) + "\n")
    file_out.write(str(thread["Starting plane"]) + "\n")
    file_out.write(str(thread["Threads per inch"]) + "\n")

    file_out.write(str(tool["Tool diameter"]) + "\n")
    file_out.write(str(tool["Number of flutes"]) + "\n")
    file_out.write(str(tool["Speed"]) + "\n")
    file_out.write(str(tool["Feed"]) + "\n")

    file_out.write(number_of_passes + "\n")
    file_out.write(finish_passes + "\n")


def main():
    try:
        g_code_name = input("Name for g-code file:\n")
        with open(g_code_name, "w") as g_code_file:
            file_base = os.path.splitext(g_code_file.name)
            config_name = file_base[0] + ".cfg"

            thread_info = get_thread_info()
            tool_info = get_tool_info()
            if tool_info["Tool diameter"] > thread_info["Minor diameter"]:
                raise ValueError("Tool diameter must be less than Minor diameter.")
            number_of_passes = input("Number of passes (1, 2, 3, or 4):\n")
            pass_percentages = get_pass_percentages(number_of_passes)
            finish_passes = input("Number of times to run finish pass:\n")
            if int(finish_passes) < 1:
                raise ValueError("Finish passes must be greater than 0")

            toolpath_radii = get_toolpath_radii(thread_info,
                                                pass_percentages,
                                                tool_info["Tool diameter"])
            lead_arcs = list(get_lead_radii(toolpath_radii))
            feed_adjust = list(get_feed_adjustment(toolpath_radii,
                                                   tool_info["Tool diameter"]))
            rpm = round(tool_info["Speed"] * 3.82 / tool_info["Tool diameter"])
            feed = rpm * tool_info["Feed"] * tool_info["Number of flutes"]
            fast_feed = 15.0
            pitch = 1.0 / thread_info["Threads per inch"]
            lead_z = round(.125 * pitch, 4)
            start_z = -(thread_info["Thread depth"] + lead_z)
            top_plane = thread_info["Starting plane"]

            write_begin(g_code_file, rpm)
            for index, radius in enumerate(toolpath_radii):
                write_body(g_code_file,
                           lead_arcs[index],
                           feed,
                           feed_adjust[index],
                           fast_feed,
                           top_plane,
                           start_z,
                           radius,
                           lead_z,
                           pitch)
                if index == len(toolpath_radii) - 1:
                    for count in range(int(finish_passes) - 1):
                        write_body(g_code_file,
                                   lead_arcs[index],
                                   feed,
                                   feed_adjust[index],
                                   fast_feed,
                                   top_plane,
                                   start_z,
                                   radius,
                                   lead_z,
                                   pitch)
            write_end(g_code_file)
            g_code_file.close()
            with open(config_name, "w") as config_file:
                write_config_file(config_file,
                                  config_name,
                                  thread_info,
                                  tool_info,
                                  number_of_passes,
                                  finish_passes)
                config_file.close()

    except (ValueError, FileNotFoundError) as e:
        print(e)

main()