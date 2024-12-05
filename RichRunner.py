import subprocess
import sys
import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.table import Table
from pynput import keyboard
from datetime import datetime
import os
from queue import Queue, Empty
from threading import Thread
import logging
import argparse
import requests
from time import sleep
import asyncio
import websockets

# Setup logging at the top of the file, after imports
log_filename = f"richrunner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

console = Console()



class ProcessController:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Base path: {self.base_path}")
        console.print("[yellow]ProcessController initialized[/yellow]")

        # Process state
        self.server = None
        self.client = None
        self.server_status = "Stopped"
        self.client_status = "Stopped"
        self.server_start_time = None
        self.client_start_time = None
        self.server_output = ""
        self.client_output = ""

    def format_process_info(self, process):
        if process and process.poll() is None:
            return "Running"
        return "Stopped"

    def format_output(self, output):
        if isinstance(output, str):
            lines = output.split('\n')
            return '\n'.join(lines[-10:])
        return "---"

    def generate_display(self) -> Panel:
        """Generate a new display panel with current process states"""
        layout = Layout()
        layout.split_column(
            Layout(name="server", ratio=1),
            Layout(name="client", ratio=1)
        )

        # Create fresh tables each time
        server_table = Table(
            header_style="bold blue",
            border_style="blue",
            expand=True,
        )
        server_table.add_column("Status", justify="center", width=10)
        server_table.add_column("Uptime", justify="right", width=12)
        server_table.add_column("Output", ratio=1, min_width=40)

        client_table = Table(
            show_header=True,
            header_style="bold blue",
            border_style="blue",
            expand=True,
        )
        client_table.add_column("Status", justify="center", width=10)
        client_table.add_column("Uptime", justify="right", width=12)
        client_table.add_column("Output", ratio=1, min_width=50)

        # Add rows with current state
        server_color = "green" if self.server_status == "Running" else "red"
        client_color = "green" if self.client_status == "Running" else "red"

        server_table.add_row(
            f"[{server_color}]{self.format_process_info(self.server)}[/{server_color}]\n\n",
            f"{self.get_uptime(self.server_start_time)}\n\n",
            f"{self.format_output(self.server_output)}\n\n\n\n"
        )

        client_table.add_row(
            f"[{client_color}]{self.format_process_info(self.client)}[/{client_color}]\n\n",
            f"{self.get_uptime(self.client_start_time)}\n\n",
            f"{self.format_output(self.client_output)}\n\n\n\n"
        )

        # Update layout with new tables
        layout["server"].update(
            Panel(server_table, title="[bold white]Server[/bold white]", padding=(0, 1)))
        layout["client"].update(
            Panel(client_table, title="[bold white]Client[/bold white]", padding=(0, 1)))

        return Panel(layout, title="[bold white]WebSocket TTS Monitor[/bold white]", padding=(0, 1))

    def startup(self):
        self.toggle_server()
        self.toggle_client()

    def toggle_server(self):
        if self.server is None:
            console.print("[blue]Starting server...[/blue]")
            venv_python = sys.executable
            self.server = subprocess.Popen(
                [venv_python, 'main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ,
                     'VIRTUAL_ENV': os.environ.get('VIRTUAL_ENV', '')}
            )
            self.server_status = "Running"
            self.server_start_time = datetime.now()
            logger.info("Server process started")
        else:
            console.print("[red]Stopping server...[/red]")
            self.server.terminate()
            self.server = None
            self.server_status = "Stopped"
            self.server_start_time = None
            logger.info("Server process stopped")

    def toggle_client(self):
        if self.client is None:
            console.print("[blue]Starting client...[/blue]")
            self.client = subprocess.Popen(
                [sys.executable, 'client.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.client_status = "Running"
            self.client_start_time = datetime.now()
        else:
            console.print("[red]Stopping client...[/red]")
            self.client.terminate()
            self.client = None
            self.client_status = "Stopped"
            self.client_start_time = None

    def get_uptime(self, start_time):
        if start_time is None:
            return "---"
        delta = datetime.now() - start_time
        return str(delta).split('.')[0]  # Remove microseconds

    def read_output(self, process):
        if process is None:
            return ""

        output = []
        try:
            # Create queues for stdout and stderr
            stdout_queue = Queue()
            stderr_queue = Queue()

            def enqueue_output(out, queue):
                try:
                    for line in iter(out.readline, b''):
                        decoded = line.decode('utf-8', errors='replace').strip()
                        if decoded:
                            # Fix: Store output based on which process we're reading
                            if process == self.server:
                                self.server_output = decoded if out == process.stdout else f"[red]ERROR: {decoded}[/red]"
                            elif process == self.client:
                                self.client_output = decoded if out == process.stdout else f"[red]ERROR: {decoded}[/red]"
                            queue.put(decoded)
                            # logger.info(f"Process output: {decoded}")
                except Exception as e:
                    logger.error(f"Error in enqueue_output: {e}")
                finally:
                    out.close()

            # Start threads to read output
            Thread(target=enqueue_output, args=(
                process.stdout, stdout_queue), daemon=True).start()
            Thread(target=enqueue_output, args=(
                process.stderr, stderr_queue), daemon=True).start()

            # Try to get any immediate output
            try:
                while True:
                    line = stdout_queue.get_nowait()
                    if line:
                        output.append(line)
            except Empty:
                pass

            try:
                while True:
                    line = stderr_queue.get_nowait()
                    if line:
                        output.append(f"[red]ERROR: {line}[/red]")
            except Empty:
                pass

        except Exception as e:
            logger.error(f"Error reading output: {e}")

        # Keep last 10 lines
        result = "\n".join(output[-10:]) if output else ""
        return result


def wait_for_server(controller, timeout_seconds=30, interval=0.5):
    """Wait for server to be ready"""
    logger.info(f"Waiting for server (timeout: {timeout_seconds}s)")
    start_time = time.time()

    while time.time() - start_time < float(timeout_seconds):
        try:
            # Check if process is still running
            if controller.server.poll() is not None:
                logger.error("Server process has terminated!")
                return False

            # Try HTTP endpoint
            response = requests.get('http://localhost:8123/tts')
            if response.status_code == 200:
                logger.info("Server is ready!")
                return True

        except requests.exceptions.ConnectionError:
            logger.debug("Server not ready yet")
            time.sleep(interval)

    logger.error("Server failed to start")
    return False


def main():
    console = Console()
    try:
        controller = ProcessController()

        # Start processes
        controller.toggle_server()
        if wait_for_server(controller, timeout_seconds=30):
            controller.toggle_client()
            time.sleep(0.5)

            with Live(
                controller.generate_display(),
                refresh_per_second=1,  # Lower refresh rate
                console=console,
                vertical_overflow="visible",
            ) as live:
                while True:
                    if controller.server and controller.server.poll() is None:
                        server_output = controller.read_output(controller.server)
                        if server_output:
                            controller.server_output = server_output

                    if controller.client and controller.client.poll() is None:
                        client_output = controller.read_output(controller.client)
                        if client_output:
                            controller.client_output = client_output
                    live.update(controller.generate_display())
                    time.sleep(1)  # Match the refresh rate

    except KeyboardInterrupt:
        console.print("\n[red]Shutting down...[/red]")
    finally:
        if controller and controller.server:
            controller.server.terminate()
        if controller and controller.client:
            controller.client.terminate()


def test_main():
    try:
        pc = ProcessController()
        console.print("[green]Starting test mode...[/green]")

        # Start processes
        pc.toggle_server()
        pc.toggle_client()

        # Main display loop
        with Live(pc.generate_display(), refresh_per_second=4) as live:
            while True:
                if pc.server and pc.server.poll() is None:
                        server_output = pc.read_output(pc.server)
                        if server_output:
                            pc.server_output = server_output

                if pc.client and pc.client.poll() is None:
                    client_output = pc.read_output(pc.client)
                    if client_output:
                        pc.client_output = client_output
                try:
                    live.update(pc.generate_display())
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    break

    except Exception as e:
        console.print(f"[red]Error in test_main: {e}[/red]")
    finally:
        # Cleanup
        if pc.server:
            pc.server.terminate()
        if pc.client:
            pc.client.terminate()
        console.print("[yellow]Test mode ended[/yellow]")


if __name__ == "__main__":
    try:
        test_main()
        # main()
    except KeyboardInterrupt:
        console.print("\n[red]Shutting down...[/red]")
        sys.exit(0)
