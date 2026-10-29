"""Docker runtime utilities for CodeView developer sandboxes."""

# Run operating system commands safely without a shell.
import subprocess


class DockerRuntime:
    """Communicate with the Docker engine."""

    def check_docker(self):
        """Check whether Docker is installed and accessible."""

        try:
            # Ask Docker for its server version.
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],

                # Capture the command's output.
                capture_output=True,

                # Return output as text.
                text=True,

                # Stop waiting after five seconds.
                timeout=5,

                # Raise an error if Docker fails.
                check=True,
            )

            # Return the Docker server version.
            return result.stdout.strip()

        except (
            FileNotFoundError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ) as error:

            # Report that Docker is unavailable.
            raise RuntimeError(
                "Docker is not available."
            ) from error
    
    def build_container_command(self, container_name, image_name):
        """Build a restricted Docker container command."""

        # Import the sandbox security configuration.
        from server_runner.runner_service.sandbox.security import (
            get_sandbox_security_config,
        )

        # Get the configured security limits.
        security = get_sandbox_security_config()

        # Validate the container name.
        import re

        if not isinstance(container_name, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}",
            container_name,
        ):
            raise ValueError("Invalid container name.")

        # Only allow our approved developer image.
        if image_name != "ghcr.io/danielakpa/codeview-developer:dev":
            raise ValueError("Unapproved container image.")

        # Build the Docker command.
        command = [
            "docker",
            "create",

            # Give the container a name.
            "--name", container_name,

            # Limit available memory.
            "--memory", f"{security.memory_limit_mb}m",

            # Limit CPU usage.
            "--cpus", str(security.cpu_limit),

            # Limit the number of processes.
            "--pids-limit", str(security.process_limit),

            # Disable container networking.
            "--network", "none",

            # Prevent privilege escalation.
            "--security-opt", "no-new-privileges:true",

            # Drop Linux capabilities.
            "--cap-drop", "ALL",

            # Prevent writing to the container's root filesystem.
            "--read-only",


            # Provide a small temporary directory.
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",

            # Use a non-root user.
            "--user", "10001:10001",

            # Use the approved developer image.
            image_name,
        ]

        # Return the command without executing it.
        return command
    def validate_container_command(self, command):
        """Check that the Docker command contains required restrictions."""

        # Make sure the command is a list.
        if not isinstance(command, list):
            raise ValueError("Docker command must be a list.")

        # Make sure the command starts with docker create.
        if command[:2] != ["docker", "create"]:
            raise ValueError("Invalid Docker command.")

        # Define the restrictions we expect.
        required_options = {
            "--memory",
            "--cpus",
            "--pids-limit",
            "--network",
            "--cap-drop",
            "--read-only",
            "--user",
            "--security-opt",
        }

        # Check that all required options exist.
        missing = required_options - set(command)

        # Reject commands with missing restrictions.
        if missing:
            raise ValueError(
                f"Missing Docker security options: {sorted(missing)}"
            )

        # Return True when the basic checks pass.
        return True    

    def create_container(self, container_name, image_name):
        """Create a Docker container using the approved configuration."""

        # Step 1: Build the Docker command.
        command = self.build_container_command(
            container_name=container_name,
            image_name=image_name,
        )

        # Step 2: Validate the command.
        self.validate_container_command(command)

        # Step 3: Execute the Docker command.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        # Step 4: Return the newly created container ID.
        return result.stdout.strip()        


    def start_container(self, container_id):
        """Start an existing Docker container."""

        # Only accept Docker's full 64-character hexadecimal container ID.
        import re

        if not isinstance(container_id, str) or not re.fullmatch(
            r"[a-fA-F0-9]{64}",
            container_id,
        ):
            raise ValueError("Invalid container ID.")

        # Prepare the Docker start command.
        command = [
            "docker",
            "start",
            container_id,
        ]

        # Ask Docker to start the container.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        # Return the container ID.
        return result.stdout.strip()

    def stop_container(self, container_id):
        """Stop a running Docker container."""

        # Validate the container ID.
        import re

        if not isinstance(container_id, str) or not re.fullmatch(
            r"[a-fA-F0-9]{64}",
            container_id,
        ):
            raise ValueError("Invalid container ID.")

        # Prepare the Docker stop command.
        command = [
            "docker",
            "stop",

            # Allow five seconds for graceful shutdown.
            "--time", "5",

            container_id,
        ]

        # Ask Docker to stop the container.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )

        # Return the container ID.
        return result.stdout.strip()        