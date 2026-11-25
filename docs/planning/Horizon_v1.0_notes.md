# Horizon v1.0 Notes

### Introduction
Horizon v1.0 is going to be the best (server-side) digital twin I can build. I'm not going to atempt any of my crazier ideas until v2.0. However, here's a better explaination of where I want to see the Horizon project ultimately go.

## Use Case
The UxS industry is moving towards fully-autonomous swarms of drones operating beyond visual line of sight (BVLOS) in disconnected, intermitent, and limited bandwidth (DIL) environments.

Horizon aims to support this paradigm. It's philosophy is, drones should be able to understand their environment on their own, without talking to a central server.  

If anything, in a Horizon UxS the ground control system merely views the drone's world model when connectivity is available. It sees the world through the drone's eyes, rather than acts as its hive-mind.

The UxV should be able to boot up and immediately begin constructing a world model. If it has a world model saved, it will start with that. If it has a connection to mission control, or other drones in the swarm, it will download their latest world model and start with that. If it has access to the internet it will gather information on line. However, regardless of where it starts it will dynamically refine its world model based on its experience, and AI guided exploration.

## Horizon Roadmap

- Digital Shadow (Server-Side)
- Digital Twin (Server-Side)
- Digital Twin (Drone-Side)
- Wierd (Fun) Philosophy Stuff
