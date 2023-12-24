"""GUI widgets for handling divine conditions"""

from typing import Iterable

import customtkinter as ctk

from .conditions import (
    GenericCondition,
    build_buried_treasure_condition,
)


class NetherFossilDialog(ctk.CTkInputDialog):
    """Input dialog for entering the X coordinate of a 0,0 nether fossil"""

    def __init__(self, condition_list, *args, **kwargs):
        super().__init__(
            *args,
            title="Nether Fossil",
            text="Enter the X coordinate of the nether fossil",
            **kwargs,
        )
        self.condition_list = condition_list
        self.get_input()

    def get_input(self):
        try:
            value = int(super().get_input())
            self.condition_list.add_condition(
                GenericCondition(0, 16, value, 0.0),
                name=f"Nether Fossil X {value}",
                display_salt=False,
                display_int_rand=False,
                display_float_rand=False,
            )
        except ValueError:
            pass


class DecoratorDialog(ctk.CTkInputDialog):
    """Input dialog for entering the X coordinate of a 0,0 80k decorator"""

    def __init__(self, condition_list, *args, **kwargs):
        super().__init__(
            *args,
            title="80000 Decorator",
            text="Enter the X coordinate of the decorator",
            **kwargs,
        )
        self.condition_list = condition_list
        self.get_input()

    def get_input(self):
        try:
            value = int(super().get_input())
            self.condition_list.add_condition(
                GenericCondition(80000, 16, value, 0.0),
                name=f"80k Decorator X {value}",
                display_salt=False,
                display_int_rand=False,
                display_float_rand=False,
            )
        except ValueError:
            pass


class DiskDialog(ctk.CTkInputDialog):
    """Input dialog for entering the X coordinate of a 0,0 60k disk"""

    def __init__(self, condition_list, *args, **kwargs):
        super().__init__(
            *args,
            title="60000 Disk",
            text="Enter the X coordinate of the disk",
            **kwargs,
        )
        self.condition_list = condition_list
        self.get_input()

    def get_input(self):
        try:
            value = int(super().get_input())
            self.condition_list.add_condition(
                GenericCondition(60000, 16, value, 0.0),
                name=f"60k Disk Decorator X {value}",
                display_salt=False,
                display_int_rand=False,
                display_float_rand=False,
            )
        except ValueError:
            pass


class ChanceDecoratorDialog(ctk.CTkInputDialog):
    """Input dialog for entering the Z coordinate of a 0,0 10% 80k chance decorator"""

    def __init__(self, condition_list, *args, **kwargs):
        super().__init__(
            *args,
            title="10% 80k Chance Decorator",
            text="Enter the Z coordinate of the decorator",
            **kwargs,
        )
        self.condition_list = condition_list
        self.get_input()

    def get_input(self):
        try:
            value = int(super().get_input())
            self.condition_list.add_condition(
                GenericCondition(80000, 16, value, 0.1),
                name=f"10% 80k Decorator Z {value}",
                display_salt=False,
                display_int_rand=False,
                display_float_rand=False,
            )
        except ValueError:
            pass


class BuriedTreasureDialog(ctk.CTkInputDialog):
    """Input dialog for entering buried treasure coordinates"""

    def __init__(self, condition_list, *args, **kwargs):
        super().__init__(
            *args,
            title="Buried Treasure",
            text="Enter the chunk coordinates of the buried treasure seperated by a space",
            **kwargs,
        )
        self.condition_list = condition_list
        self.get_input()

    def get_input(self):
        try:
            value = super().get_input()
            chunk_x, chunk_z = tuple(int(c) for c in value.split(" "))
            self.condition_list.add_condition(
                build_buried_treasure_condition(chunk_x, chunk_z),
                name=f"Buried Treasure {chunk_x},{chunk_z}",
                display_salt=False,
                display_int_rand=False,
                display_float_rand=False,
            )
        except ValueError:
            pass


class ConditionList(ctk.CTkScrollableFrame):
    """Scrollable list of ConditionWidget"""

    def __init__(
        self, *args, width: int = 500, height: int = 500, command=None, **kwargs
    ):
        super().__init__(*args, width, height, **kwargs)
        self.command = command
        self.widgets: list[ConditionWidget] = []
        self.add_condition_button = ctk.CTkButton(
            self,
            text="Add Generic Condition",
            command=lambda *_: self.add_condition(GenericCondition(0, 0, 0, 0.0)),
        )
        self.add_condition_button.pack(side="bottom")

    def add_condition(self, condition, **kwargs):
        """Add a condition to the list and create a widget for it"""
        self.widgets.append(ConditionWidget(self, condition, **kwargs))
        self.widgets[-1].pack()
        if self.command is not None:
            self.command()

    def remove_widget(self, widget):
        """Remove widget and its condition from the list"""
        widget.pack_forget()
        idx = self.widgets.index(widget)
        self.widgets.pop(idx)
        if self.command is not None:
            self.command()

    @property
    def conditions(self) -> Iterable[GenericCondition]:
        """Return a generator that iterates over all GenericConditions of the widgets in the list"""
        return (widget.condition for widget in self.widgets)


class ConditionWidget(ctk.CTkFrame):
    """GUI widget for handling a divine condition"""

    def __init__(
        self,
        master: ConditionList,
        condition: GenericCondition,
        *args,
        width: int = 1000,
        height: int = 50,
        display_int_rand: bool = True,
        display_float_rand: bool = True,
        display_salt: bool = True,
        name: str = None,
        **kwargs,
    ):
        super().__init__(master, *args, width, height, **kwargs)

        if name:
            self.name_label = ctk.CTkLabel(self, text=name)
            self.name_label.pack(side="left", padx=5)

        self.salt_entry = ctk.CTkEntry(
            self,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.salt_entry.insert(0, str(condition.salt))
        if display_salt:
            self.salt_entry.pack(side="left", padx=5)

        self.int_maximum_entry = ctk.CTkEntry(
            self,
            70,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.int_maximum_entry.insert(0, str(condition.int_maximum))
        if display_int_rand:
            self.int_maximum_entry.pack(side="left", padx=5)

        self.int_value_entry = ctk.CTkEntry(
            self,
            70,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.int_value_entry.insert(0, str(condition.int_value))
        if display_int_rand:
            self.int_value_entry.pack(side="left", padx=5)

        self.float_maximum_entry = ctk.CTkEntry(self, 70)
        self.float_maximum_entry.insert(0, str(condition.float_maximum))
        if display_float_rand:
            self.float_maximum_entry.pack(side="left", padx=5)

        self.delete_button = ctk.CTkButton(
            self, text="Delete", command=lambda *_: self.master.remove_widget(self)
        )
        self.delete_button.pack(side="right", padx=5)

    @property
    def condition(self) -> GenericCondition:
        """Build a GenericCondition from the widget's entries"""
        try:
            return GenericCondition(
                int(self.salt_entry.get()),
                int(self.int_maximum_entry.get()),
                int(self.int_value_entry.get()),
                float(self.float_maximum_entry.get()),
            )
        except ValueError:
            return GenericCondition(0, 0, 0, 0.0)
