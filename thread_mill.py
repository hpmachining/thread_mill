#!python3
"""Create g-code sub-program to cut internal threads with single pass tool."""

import math
import os


class ScrewThread(object):
    """A class to store attributes needed to define a screw thread."""

    # pylint: disable=too-many-arguments
    def __init__(self, major=0.0, minor=0.0, depth=0.0, start=0.0, pitch=0.0):
        """Initialize the attributes.

        Keyword args:
            major: Major diameter.
            minor: Minor diameter.
            depth: Relative depth.
            start: Absolute value of starting plane.
            pitch: Number of threads per inch (TPI).
        """
        self.major_diameter = major
        self.minor_diameter = minor
        self.depth = depth
        self.start_plane = start
        self.tpi = 0.0
        self.pitch = pitch

    def input_thread_info(self):
        """Prompt for and validate the attributes of a screw thread.

        Raises:
            ValueError: If data is not able to convert to float,
            if minor_diameter is not less than major_diameter,
            or if any value other than starting_plane is not greater
            than zero.
        """
        self.major_diameter = input('Major diameter:\n')
        self.minor_diameter = input('Minor diameter:\n')
        self.depth = input('Thread depth:\n')
        self.start_plane = input('Starting plane:\n')
        self.tpi = input('Pitch in threads per inch:\n')
        self.pitch = 1.0 / float(self.tpi)
        self.validate()

    def validate(self):
        """Convert attributes to float and validate.

        Raises:
            ValueError: If data is not able to convert to float,
            if minor_diameter is not less than major_diameter,
            or if any value other than starting_plane is not greater
            than zero.
        """
        try:
            for key, value in vars(self).items():
                vars(self)[key] = float(value)
                if key != 'start_plane' and float(value) <= 0.0:
                    raise ValueError(key + ' must be > 0.0')
            if self.minor_diameter >= self.major_diameter:
                raise ValueError('Minor diameter must be less than Major diameter')
        except ValueError:
            raise


class CuttingTool(object):
    """A class to store the attributes of a cutting tool."""

    def __init__(self, diameter=0.0, flutes=0.0, speed=0.0, feed=0.0):
        """Initialize the attributes.

        Keyword args:
            diameter: Diameter of cutting tool.
            flutes: Number of flutes.
            speed: The speed in surface feet per minute(SFM).
            feed: Feed rate given in feed per tooth.
        """
        self.diameter = diameter
        self.flutes = flutes
        self.speed = speed
        self.feed = feed
        self.rpm = 0.0

    def input_tool_info(self):
        """Prompt for and validate the attributes of a cutting tool.

        Raises:
            ValueError: If data is not able to convert to float or if
            any value is not greater than zero.
        """
        self.diameter = input('Tool diameter:\n')
        self.flutes = input('Number of flutes:\n')
        self.speed = input('Speed in surface feet per minute (SFM):\n')
        self.feed = input('Feed per tooth:\n')
        self.rpm = float(self.speed) * 3.82 / float(self.diameter)
        self.validate()

    def validate(self):
        """Convert attributes to float and validate.

        Raises:
            ValueError: If data is not able to convert to float or if
            any value is not greater than zero.
        """
        try:
            for key, value in vars(self).items():
                vars(self)[key] = float(value)
                if float(value) <= 0.0:
                    raise ValueError(key + ' must be > 0.0')
        except ValueError:
            raise


class BodyDetails(object):
    """Calculate and store the toolpath details.

    Calculates and stores the information needed for writing the main body
    of the g-code sub-program.
    """

    def __init__(self, thread, tool, number_of_passes=1):
        """Initialize the attributes.

        Args:
            thread (ScrewThread): The screw thread object to machine.
            tool (CuttingTool): The tool object to use to machine the screw thread.

        Keyword args:
            number_of_passes (int): Number of radial steps to use to machine
                the screw thread.
        """
        try:
            thread.validate()
            tool.validate()
            if tool.diameter > thread.minor_diameter:
                raise ValueError('Tool diameter must be less than Minor diameter.')
            self.passes = self.calc_pass_percentages(number_of_passes)
            self.radii = self.calc_toolpath_radii(thread, self.passes, tool.diameter)
            self.lead_arcs = self.calc_lead_arcs(self.radii)
        except ValueError:
            raise

        self.feed = self.calc_feed_rate(tool)
        self.top_plane = thread.start_plane
        self.lead_z = round(.125 * thread.pitch, 4)
        self.start_z = -(thread.depth + self.lead_z)

    def calc_adjusted_feed(self, tool):
        """Calculate the feed rate factor for proper feed per tooth.

        Feed rates are applied at the center of the tool. When cutting an internal
        thread, the feed at the outside of the tool is faster than at the center.
        This function will calculate the factor to use to adjust the feed rate to
         get the desired feed per tooth.

        Args:
            tool (CuttingTool): The cutting tool data.

        Returns:
            A list of adjusted feed rates for the given toolpath radii
            and tool diameter.
        """
        adjusted_feed = []
        for radius in self.radii:
            adjusted_feed.append(
                tool.feed * (radius * 2.0) / (radius * 2.0 + tool.diameter)
            )
        return adjusted_feed

    def calc_feed_rate(self, tool):
        """Calculate the feed rate in inches per minute.

        Args:
            tool (CuttingTool): The cutting tool data.
        """
        feeds = self.calc_adjusted_feed(tool)
        feed_rates = []
        for feed_per_tooth in feeds:
            feed_rates.append(feed_per_tooth * tool.flutes * tool.rpm)
        return feed_rates

    @staticmethod
    def calc_pass_percentages(passes):
        """Return a list of percentages to be used for radial depth of cut.

        Return a list of floats to be used as percentages of the total depth of cut
        based on the number of passes. The percentages used are meant to equalize
        side cutting pressure on the cutting tool.

        Args:
            passes: Number of radial offsets. Valid inputs are 1, 2, 3, or 4.

        Returns:
            A list containing the percentages to use for the radial
            depth of cuts based on the number of passes:
                1 pass = [1.0]
                2 passes = [.65, .35]
                3 passes = [.50, .30, .20]
                4 passes = [.40, .27, .20, .13]

        Raises:
            ValueError: If passes is not representable as int or if passes
                value is not 1, 2, 3 or 4
        """
        try:
            if not 0 < int(passes) < 5:
                raise ValueError
        except ValueError:
            raise ValueError(str(passes) + ' is not a valid option for number of passes.')
        if int(passes) == 1:
            return [1.0]
        elif int(passes) == 2:
            return [.65, .35]
        elif int(passes) == 3:
            return [.50, .30, .20]
        return [.40, .27, .20, .13]

    @staticmethod
    def calc_toolpath_radii(thread, passes, tool_diameter):
        """Calculate the toolpath radii.

        Calculate the radii to use for each pass of the toolpath.

        Args:
            thread (ScrewThread): A ScrewThread object.
            passes: A list of percentages to use for each pass.
            tool_diameter: Diameter of the cutting tool.

        Returns:
            A list of radii to use for toolpath.
        """
        radii = []
        total_stock = round((thread.major_diameter - thread.minor_diameter) / 2.0, 5)
        base_radius = round((thread.minor_diameter - tool_diameter) / 2.0, 5)
        previous_radius = 0.0
        for i in passes:
            current_radius = round(base_radius + total_stock * i + previous_radius, 4)
            radii.append(current_radius)
            previous_radius = current_radius - base_radius
        return radii

    @staticmethod
    def calc_lead_arcs(radii):
        """Calculate the radii for the entrance and exit arcs.

        Args:
            radii: A list of toolpath radii.

        Returns:
            A list of entrance and exit arcs to use for each pass.
        """
        sin_45 = math.sin(math.radians(45))
        arcs = []
        for radius in radii:
            arcs.append(round(radius * sin_45, 4))
        return arcs


# def calc_pass_percentages(passes):
#     """Return a list of percentages to be used for radial depth of cut.
#
#     Return a list of floats to be used as percentages of the total depth of cut
#     based on the number of passes. The percentages used are meant to equalize
#     side cutting pressure on the cutting tool.
#
#     Args:
#         passes: Number of radial offsets. Valid inputs are 1, 2, 3, or 4.
#
#     Returns:
#         A list containing the percentages to use for the radial
#         depth of cuts based on the number of passes:
#             1 pass = [1.0]
#             2 passes = [.65, .35]
#             3 passes = [.50, .30, .20]
#             4 passes = [.40, .27, .20, .13]
#
#     Raises:
#         ValueError: If passes is not representable as int or if passes
#             value is not 1, 2, 3 or 4
#     """
#     try:
#         if not 0 < int(passes) < 5:
#             raise ValueError
#     except ValueError:
#         raise ValueError(str(passes) + ' is not a valid option for number of passes.')
#     if int(passes) == 1:
#         return [1.0]
#     elif int(passes) == 2:
#         return [.65, .35]
#     elif int(passes) == 3:
#         return [.50, .30, .20]
#     return [.40, .27, .20, .13]


# def calc_toolpath_radii(thread, passes, tool_diameter):
#     """Calculate the toolpath radii.
#
#     Calculate the radii to use for each pass of the toolpath.
#
#     Args:
#         thread (ScrewThread): A ScrewThread object.
#         passes: A list of percentages to use for each pass.
#         tool_diameter: Diameter of the cutting tool.
#     """
#     radii = []
#     total_stock = round((thread.major_diameter - thread.minor_diameter) / 2.0, 5)
#     base_radius = round((thread.minor_diameter - tool_diameter) / 2.0, 5)
#     previous_radius = 0.0
#     for i in passes:
#         current_radius = round(base_radius + total_stock * i + previous_radius, 4)
#         radii.append(current_radius)
#         previous_radius = current_radius - base_radius
#     return radii


# def calc_lead_arcs(radii):
#     """Calculate the radii for the entrance and exit arcs.
#
#     Args:
#         radii: A list of toolpath radii.
#
#     Returns:
#         A map of entrance and exit arcs to use for each pass.
#     """
#     sin_45 = math.sin(math.radians(45))
#     return map(lambda lead: round(lead * sin_45, 4), radii)


# def calc_feed_adjustment(radii, tool_diameter):
#     """Calculate the feed rate factor for proper feed per tooth.
#
#     Feed rates are applied at the center of the tool. When cutting an internal
#     thread, the feed at the outside of the tool is faster than at the center.
#     This function will calculate the factor to use to adjust the feed rate to
#      get the desired feed per tooth.
#
#     Args:
#         radii: A list of toolpath radii.
#         tool_diameter: Diameter of the cutting tool.
#
#     Returns:
#         A map of feed rate adjustment factors for each toolpath radius.
#     """
#     return map(lambda adjust: (adjust * 2.0) / (adjust * 2.0 + tool_diameter), radii)


def post_begin(rpm):
    """Format the beginning of the g-code sub-program.

    Args:
        rpm: The speed to use in revolutions per minute.
    """
    begin_out = 'S{} M3\n\n'.format(round(rpm))
    return begin_out


def post_body(toolpath, thread, finish_passes, rapid_feed=15.0):
    """Write the main body of the g-code sub-program."""
    g_code_out = ''
    g_code = ''
    top_plane = str(toolpath.top_plane)
    rapid_feed = round(rapid_feed, 4)
    pitch = str(round(thread.pitch, 4))
    for radius, lead_arc, feed in zip(toolpath.radii, toolpath.lead_arcs, toolpath.feed):
        feed = round(feed, 4)
        start_x = round(lead_arc * math.sin(math.radians(45)), 4)
        start_y = -start_x
        g_code = (
            'G90 G0 Z{}\n'.format(top_plane)
            + 'G91 G01 Z{} F{}\n'.format(toolpath.start_z, rapid_feed)
            + 'G01 X{} Y{} F{}\n'.format(start_x, start_y, feed)
            + 'G03 X{} Y{} Z{} I0.0 J{} F{}\n'.format(
                round(radius - start_x, 4), -start_y, toolpath.lead_z, -start_y, feed)
            + 'G03 X0.0 Y0.0 Z{} I{} J0.0 F{}\n'.format(pitch, round(-radius, 4), feed)
            + 'G03 X{} Y{} Z{} I{} J0.0 F{}\n'.format(
                -start_x, -start_y, toolpath.lead_z, -start_x, feed)
            + 'G01 X{} Y{} F{}\n\n'.format(-start_x, start_y, rapid_feed)
        )
        g_code_out += g_code
    if finish_passes > 1:
        for _ in range(finish_passes - 1):
            g_code_out += g_code
    return g_code_out


def post_end():
    """Format the end of the g-code sub-program."""
    end_out = 'M99\n%\n'
    return end_out


# pylint: disable=too-many-arguments
def write_config_file(file_out,
                      file_name,
                      thread,
                      tool,
                      number_of_passes,
                      finish_passes):
    """Save all the inputs in a file."""
    file_out.write(file_name + '\n')
    file_out.write(str(thread.major_diameter) + '\n')
    file_out.write(str(thread.minor_diameter) + '\n')
    file_out.write(str(thread.depth) + '\n')
    file_out.write(str(thread.start_plane) + '\n')
    file_out.write(str(thread.tpi) + '\n')

    file_out.write(str(tool.diameter) + '\n')
    file_out.write(str(tool.flutes) + '\n')
    file_out.write(str(tool.speed) + '\n')
    file_out.write(str(tool.feed) + '\n')

    file_out.write(number_of_passes + '\n')
    file_out.write(finish_passes + '\n')


def main():
    """Command line implementation."""
    try:
        g_code_name = input('Name for g-code file:\n')
        with open(g_code_name, 'w') as g_code_file:
            file_base = os.path.splitext(g_code_file.name)
            config_name = file_base[0] + '.cfg'
            thread = ScrewThread()
            thread.input_thread_info()
            tool = CuttingTool()
            tool.input_tool_info()
            number_of_passes = input('Number of passes (1, 2, 3, or 4):\n')
            toolpath = BodyDetails(thread, tool, int(number_of_passes))
            finish_passes = input('Number of times to run finish pass:\n')
            if int(finish_passes) < 1:
                raise ValueError('Finish passes must be greater than 0')
            with open(config_name, 'w') as config_file:
                write_config_file(config_file,
                                  g_code_name,
                                  thread,
                                  tool,
                                  number_of_passes,
                                  finish_passes)
                config_file.close()

            g_code_file.write(post_begin(tool.rpm))
            g_code_file.write(post_body(toolpath, thread, int(finish_passes), 20.0))
            g_code_file.write(post_end())
            g_code_file.close()
    except (ValueError, FileNotFoundError) as ex:
        print(ex)


def main_2():
    """Dummy test function."""
    thread = ScrewThread()
    thread.input_thread_info()
    # print(get_thread_info())
    print(thread.__dict__)


if __name__ == '__main__':
    main()
