"""GUI widgets for handling divine conditions"""

from typing import Iterable
import numpy as np
from functools import partial

import customtkinter as ctk

from .conditions import (
    GenericConditionSet,
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
            self.condition_list.add_nether_fossil_condition(int(super().get_input()))
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
            self.condition_list.add_decorator_condition(int(super().get_input()))
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
            self.condition_list.add_disk_decorator_condition(int(super().get_input()))
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
            self.condition_list.add_chance_decorator_condition(int(super().get_input()))
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
            self.condition_list.add_buried_treasure_condition(chunk_x, chunk_z)
        except (ValueError, AttributeError):
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
            command=lambda *_: self.add_condition(GenericConditionSet()),
        )
        self.add_condition_button.pack(side="bottom")

    def add_nether_fossil_condition(self, x):
        self.add_condition(
            GenericCondition(0, 16, x, 0.0),
            name=f"Nether Fossil X {x}",
            display_salt=False,
            display_int_rand=False,
            display_float_rand=False,
        )

    def add_decorator_condition(self, x):
        self.add_condition(
            GenericCondition(80000, 16, x, 0.0),
            name=f"80k Decorator X {x}",
            display_salt=False,
            display_int_rand=False,
            display_float_rand=False,
        )

    def add_disk_decorator_condition(self, x):
        self.add_condition(
            GenericCondition(60000, 16, x, 0.0),
            name=f"60k Disk Decorator X {x}",
            display_salt=False,
            display_int_rand=False,
            display_float_rand=False,
        )

    def add_chance_decorator_condition(self, z):
        self.add_condition(
            GenericCondition(80000, 16, z, 0.1),
            name=f"10% 80k Decorator Z {z}",
            display_salt=False,
            display_int_rand=False,
            display_float_rand=False,
        )

    def add_buried_treasure_condition(self, chunk_x, chunk_z):
        self.add_condition(
            build_buried_treasure_condition(chunk_x, chunk_z),
            labels=("", "", "", ""),
            name=f"Buried Treasure {chunk_x},{chunk_z}",
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

    def clear(self):
        """Remove all widgets and conditions from the list"""
        while self.widgets:
            self.widgets.pop().pack_forget()
        if self.command is not None:
            self.command()

    @property
    def conditions(self) -> Iterable[GenericConditionSet]:
        """Return a generator that iterates over all GenericConditionSets of the widgets in the list"""
        return (
            widget.condition for widget in self.widgets if widget.enabled_checkbox.get()
        )


class ConditionWidget(ctk.CTkFrame):
    """GUI widget for handling a divine condition"""

    def __init__(
        self,
        master: ConditionList,
        condition: GenericConditionSet,
        *args,
        name="Generic Condition",
        labels=("R1", "R2", "R3", "R4"),
        types=(None, None, None, None),
        width: int = 1000,
        height: int = 50,
        **kwargs,
    ):
        super().__init__(master, *args, width, height, **kwargs)

        self.name_label = ctk.CTkLabel(self, text=name)
        self.name_label.grid(row=0, column=0)

        self.salt_entry = ctk.CTkEntry(
            self,
            validate="all",
            validatecommand=(
                self.register(
                    lambda v: v[1:].isdigit() if v[0] == "-" else v.isdigit()
                ),
                "%P",
            ),
        )
        self.salt_entry.insert(0, str(condition.salt))
        self.salt_entry.grid(row=0, column=1)

        self.enabled_checkbox = ctk.CTkCheckBox(self, text="Enabled")
        self.enabled_checkbox.select()
        self.enabled_checkbox.grid(row=0, column=2)

        self.int_value_entries = []
        self.int_maximum_entries = []
        self.float_minimum_entries = []
        self.float_maximum_entries = []

        for i, (c, label, ctype) in enumerate(zip(condition[1:], labels, types)):
            type_selector = None
            if label:
                if ctype is None:

                    def callback(i, value):
                        self.int_value_entries[i].grid_forget()
                        self.int_maximum_entries[i].grid_forget()
                        self.float_minimum_entries[i].grid_forget()
                        self.float_maximum_entries[i].grid_forget()
                        if value == "int":
                            self.int_value_entries[i].grid(row=i + 1, column=1)
                            self.int_maximum_entries[i].grid(row=i + 1, column=2)
                        else:
                            self.float_minimum_entries[i].grid(row=i + 1, column=1)
                            self.float_maximum_entries[i].grid(row=i + 1, column=2)

                    type_selector = ctk.CTkComboBox(
                        self, values=["int", "float"], command=partial(callback, i)
                    )
                    type_selector.grid(row=i + 1, column=0)
                else:
                    ctk.CTkLabel(self, text=label).grid(row=i + 1, column=0)
            int_value_entry = ctk.CTkEntry(
                self,
                70,
                validate="all",
                validatecommand=(self.register(str.isdigit), "%P"),
            )
            int_value_entry.insert(0, str(c.int_value))
            int_maximum_entry = ctk.CTkEntry(
                self,
                70,
                validate="all",
                validatecommand=(self.register(str.isdigit), "%P"),
            )
            int_maximum_entry.insert(0, str(c.int_maximum))
            float_minimum_entry = ctk.CTkEntry(
                self,
                70,
            )
            float_minimum_entry.insert(0, str(c.float_minimum))
            float_maximum_entry = ctk.CTkEntry(
                self,
                70,
            )
            float_maximum_entry.insert(0, str(c.float_maximum))
            if ctype is int or (
                type_selector is not None and type_selector.get() == "int"
            ):
                if label:
                    int_value_entry.grid(row=i + 1, column=1)
                    int_maximum_entry.grid(row=i + 1, column=2)
            if ctype is float or (
                type_selector is not None and type_selector.get() == "float"
            ):
                if label:
                    float_minimum_entry.grid(row=i + 1, column=1)
                    float_maximum_entry.grid(row=i + 1, column=2)
            self.int_value_entries.append(int_value_entry)
            self.int_maximum_entries.append(int_maximum_entry)
            self.float_minimum_entries.append(float_minimum_entry)
            self.float_maximum_entries.append(float_maximum_entry)

        self.delete_button = ctk.CTkButton(
            self, text="Delete", command=lambda *_: self.master.remove_widget(self)
        )
        self.delete_button.grid(row=0, column=3)

    @property
    def condition(self) -> GenericConditionSet:
        """Build a GenericConditionSet from the widget's entries"""
        try:
            return GenericConditionSet(
                np.int64(self.salt_entry.get()),
                GenericCondition(
                    np.int64(self.int_maximum_entries[0].get()),
                    np.int64(self.int_value_entries[0].get()),
                    np.float64(self.float_minimum_entries[0].get()),
                    np.float64(self.float_maximum_entries[0].get()),
                ),
                GenericCondition(
                    np.int64(self.int_maximum_entries[1].get()),
                    np.int64(self.int_value_entries[1].get()),
                    np.float64(self.float_minimum_entries[1].get()),
                    np.float64(self.float_maximum_entries[1].get()),
                ),
                GenericCondition(
                    np.int64(self.int_maximum_entries[2].get()),
                    np.int64(self.int_value_entries[2].get()),
                    np.float64(self.float_minimum_entries[2].get()),
                    np.float64(self.float_maximum_entries[2].get()),
                ),
                GenericCondition(
                    np.int64(self.int_maximum_entries[3].get()),
                    np.int64(self.int_value_entries[3].get()),
                    np.float64(self.float_minimum_entries[3].get()),
                    np.float64(self.float_maximum_entries[3].get()),
                ),
            )
        except ValueError:
            return GenericConditionSet()
