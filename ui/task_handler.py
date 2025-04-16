import chainlit as cl


class TaskHandler:
    def __init__(self):
        self._task_list = None

    async def _get_task_list(self):
        """Lazily initialize and return the task list."""
        if self._task_list is None:
            self._task_list = cl.TaskList()
        return self._task_list

    async def send_task(self, title: str):
        """Send a task to the UI."""
        task_list = await self._get_task_list()

        task = cl.Task(title=title, status=cl.TaskStatus.DONE)
        await task_list.add_task(task)
        await task_list.send()
