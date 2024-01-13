# auto-divine-calc
Autonomous "Divine Travel" Calculator for Minecraft 1.16.1

[![](https://img.shields.io/badge/Latest%20Windows%20Build-blue)](https://nightly.link/Lincoln-LM/auto-divine-calc/workflows/main/main/Windows%20Includes%20Lib%20true%20Build.zip)
[![](https://img.shields.io/badge/Latest%20Linux%20Build-orange)](https://nightly.link/Lincoln-LM/auto-divine-calc/workflows/main/main/Linux%20Includes%20Lib%20true%20Build.zip)

![](https://github.com/Lincoln-LM/auto-divine-calc/assets/73306575/afcf8186-222f-40bf-ac37-cbc2354415e2)

Heavily based on the work by [Matthew Bolan](https://www.youtube.com/@matthewbolan8154) (and other early divine developers) and his [DivineHeatmapGenerator](https://github.com/mjtb49/DivineHeatmapGenerator).

# Disclaimer: speedrun.com Verification Pending
auto-divine-calc applies the same concepts and features as other allowed tools (DivineHeatmapGenerator, NinjabrainBot) but external tools require explicit whitelisting by speedrun.com's Minecraft moderators and they have not yet come to a decision.

## Divine Travel Video Explanation
[Divine Travel for Speedrunning - Using Animals and Bones to Predict the Stronghold. | Matthew Bolan](https://www.youtube.com/watch?v=IKo-jrZSgWU)

## Brief Explanation
Divine travel is the process of observing the characteristics and placement of particular world features (generally in the 0,0 chunk) in order to determine information about the angle and distance of the first stronghold (and by extension, first ring of strongholds) generated in a Minecraft world.

This tool models a statistical distribution via a heatmap of where strongholds most often generate on seeds that share the observed characteristics in order for speedrunners to have the best chance at exiting the nether close to a stronghold.

It is **NOT** a tool for seed cracking and cannot be used for this purpose.

auto-divine-calc aims to be an improvement upon DivineHeatmapGenerator and allows runners to automatically input divine conditions based on the ``f3+i`` and ``f3+c`` debug clipboard outputs and various keybinds the same way NinjabrainBot does now for fossil divine.