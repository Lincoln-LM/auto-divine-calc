"""GUI widgets for handling divine conditions"""

from typing import Iterable

import customtkinter as ctk

from .conditions import (
    GenericCondition,
    build_buried_treasure_condition,
    build_first_portal_condition,
    build_third_portal_condition,
)


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
        self.add_buried_treasure_condition(12, -1)
        self.add_first_portal_condition(1)
        self.add_third_portal_condition(1)

    def add_buried_treasure_condition(self, chunk_x, chunk_z):
        """Add a buried treasure condition based on chunk coordinates"""
        self.add_condition(
            build_buried_treasure_condition(chunk_x, chunk_z),
            name=f"Buried Treasure {chunk_x},{chunk_z}",
            display_int_rand=False,
        )

    def add_first_portal_condition(self, direction):
        """Add a first portal condition based on cardinal direction"""
        directions = ("East", "North", "West", "South")
        self.add_condition(
            build_first_portal_condition(direction),
            name=f"First Portal {directions[direction]}",
            display_float_rand=False,
            display_int_rand=False,
            display_salt=False,
        )

    def add_third_portal_condition(self, direction):
        """Add a third portal condition based on cardinal direction"""
        directions = ("East", "North", "West", "South")
        self.add_condition(
            build_third_portal_condition(direction),
            name=f"Third Portal {directions[direction]}",
            display_float_rand=False,
            display_int_rand=False,
            display_salt=False,
        )

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
