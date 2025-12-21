# CS-350-15254-M01-Emerging-Sys-Arch-Tech-2025


Summarize the project and what problem it was solving.
The goal of this project was to construct a functional thermostat prototype that tracks a predetermined point, measures room temperature, and displays its behavior via an LCD, LEDs, and UART output. It solves the issue of demonstrating that the fundamental low-level "thermostat brain" functions before worrying about cloud reporting and Wi-Fi.

What did you do particularly well?
I successfully assembled the hardware components into a clear off heat cool state machine and ensured that the outputs met the specifications (solid when at the set point, fade when active). Additionally, I managed the two-button restriction in a sensible manner without sacrificing the necessary functionality.

Where could you improve?
I could do a better job of organizing and testing the code, particularly with regard to threads and timing, so that when something is wired incorrectly, debugging can happen more quickly. Additionally, I would tighten up error handling for the sensor and UART to make failures visible rather than silent.

What tools and/or resources are you adding to your support network?
I am definitely keeping the gpiozero docs, Adafruit sensor and LCD docs, and a good Raspberry Pi GPIO pinout close at hand. I am also adding a simple hardware sanity check script like my button test as a go to tool before I blame the main program.

What skills from this project will be particularly transferable to other projects and or course work?

The big transferable skills are designing around a state machine, working with I2C devices, using GPIO callbacks for input and pushing structured data out over UART. That's the same mindset I'll use for other embedded projects and even for higher-level systems where you still have states and events and telemetry.

How did you make this project maintainable, readable, and adaptable? 

I have kept the logic separated into sections of responsibility, such as state behavior, display updates, input handling, and hardware tests, using clear names and comments so it's easy to follow later. I also used constants for pins and timing so that, when changing wiring or behavior, it does not turn into a hunt through the whole file.
