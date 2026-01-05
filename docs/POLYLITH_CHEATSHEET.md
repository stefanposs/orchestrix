# Polylith CLI Cheatsheet

This document provides a quick reference for using the `polylith-cli` tool to manage the Orchestrix workspace.

## Basic Concepts

*   **Workspace**: The root of the repository, containing all code.
*   **Bases**: The entry points of your applications (e.g., API handlers, CLI commands). They expose the public interface.
*   **Components**: The building blocks of your logic. They are reusable and should not depend on bases.
*   **Projects**: The deployment units. They define which bases and components are bundled together into an artifact (wheel, docker image, etc.).

## Common Commands

### Information
*   `poly info`: Shows the structure of the workspace, including projects, bases, and components, and their relationships (bricks).
*   `poly libs`: Shows third-party library dependencies for each project and brick.
*   `poly deps`: Visualizes the dependency graph.

### Creation
*   `poly create component --name <name>`: Creates a new component in `components/<namespace>/<name>`.
*   `poly create base --name <name>`: Creates a new base in `bases/<namespace>/<name>`.
*   `poly create project --name <name>`: Creates a new project in `projects/<name>`.

### Development
*   `poly check`: Validates the workspace structure and checks for missing dependencies or architectural violations (e.g., components importing bases).
*   `poly test`: Runs tests for the entire workspace or specific parts.
*   `poly sync`: Syncs dependencies (if supported by the package manager).

## Workflow Example

1.  **Create a Component**:
    ```bash
    poly create component --name mylogic
    ```
    Implement your logic in `components/orchestrix/mylogic`.

2.  **Create a Base**:
    ```bash
    poly create base --name myapi
    ```
    Implement your API in `bases/orchestrix/myapi`, importing `orchestrix.mylogic`.

3.  **Create a Project**:
    ```bash
    poly create project --name myapp
    ```
    Configure `projects/myapp/pyproject.toml` to include `bases/orchestrix/myapi` and `components/orchestrix/mylogic`.

4.  **Check & Test**:
    ```bash
    poly check
    poly test
    ```

## Reference
For more details, visit the [official documentation](https://davidvujic.github.io/python-polylith-docs/).
