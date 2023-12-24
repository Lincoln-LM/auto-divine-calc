"""GUI widgets for handling divine conditions"""

from typing import Iterable

import customtkinter as ctk

from .conditions import GenericCondition, build_buried_treasure_condition


class ConditionList(ctk.CTkScrollableFrame):
    """Scrollable list of ConditionWidget"""

    def __init__(self, *args, width: int = 500, height: int = 500, **kwargs):
        super().__init__(*args, width, height, **kwargs)
        self.widgets: list[ConditionWidget] = []
        self.add_condition_button = ctk.CTkButton(
            self,
            text="Add Generic Condition",
            command=lambda *_: self.add_condition(GenericCondition(0, 0, 0, 0.0)),
        )
        self.add_condition_button.pack(side="bottom")
        self.add_condition(build_buried_treasure_condition(12, -1), has_int_rand=False)

    def add_condition(self, condition, **kwargs):
        """Add a condition to the list and create a widget for it"""
        self.widgets.append(ConditionWidget(self, condition, **kwargs))
        self.widgets[-1].pack()

    def remove_widget(self, widget):
        """Remove widget and its condition from the list"""
        widget.pack_forget()
        idx = self.widgets.index(widget)
        self.widgets.pop(idx)

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
        has_int_rand: bool = True,
        has_float_rand: bool = True,
        **kwargs
    ):
        super().__init__(master, *args, width, height, **kwargs)

        self.salt_entry = ctk.CTkEntry(
            self,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.salt_entry.insert(0, str(condition.salt))
        self.salt_entry.pack(side="left")

        self.int_maximum_entry = ctk.CTkEntry(
            self,
            70,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.int_maximum_entry.insert(0, str(condition.int_maximum))
        if has_int_rand:
            self.int_maximum_entry.pack(side="left")

        self.int_value_entry = ctk.CTkEntry(
            self,
            70,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.int_value_entry.insert(0, str(condition.int_value))
        if has_int_rand:
            self.int_value_entry.pack(side="left")

        self.float_maximum_entry = ctk.CTkEntry(self, 70)
        self.float_maximum_entry.insert(0, str(condition.float_maximum))
        if has_float_rand:
            self.float_maximum_entry.pack(side="left")

        self.delete_button = ctk.CTkButton(
            self, text="Delete", command=lambda *_: self.master.remove_widget(self)
        )
        self.delete_button.pack(side="right")

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
