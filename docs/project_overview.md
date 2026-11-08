# Horizon Project Overview

## Project Summary
Horizon is a platform for creating digital twins of a drone's environment.

A drone's digital twin of its environment is called a horizon model. Horizon models serve three purposes:

- __Represent World State__:
A horizon model maintains an accurate representation of the state of the drone's environment.
- __Manipulate World State__:
A horizon model defines actions that drones can take within their environment. 
- __Enable Counterfactual Reasoning__:
A horizon model enables drones to reason about might happen in the future or may have happened in the past.

In the long run Horizon is intended to support autonomous drone operations by serving as the "world model" within model based agents. Ideally, drones will be able to use Horizon to model their environments, share their models, and build a collective understanding of the "situation on the ground" in real time on the edge.

For now though, that's just a dream.

The present iteration of Horizon is a portfolio project I'm working on to build my skills and hopefully get a job. It's focus will be entirely on simulating low altitude airspace in real-time using a variety of data sources. The resulting horizon model will not be used by a model based agent to represent, manipulate, or reason about its environment.

## Background & Motivation

The name "Horizon" has a double meaning. It refers to the place where the sky meets the land. It also refers to the limit of a subject's perception, the limit of its imperfect but still valid understanding of the world around it.

This double meaning reflects two of Horizon's key aspirations:

1) To model and simulate drone operations in low altitude environments where terrain matters.
2) To model an autonomous agent's knowledge of its world, which is by definition both geographically and ontologically bounded.

## Scope

This section is more for my own sake than anyone else's.

When I use the term "Horizon" I have typically had three related, overlapping, but nevertheless distinct projects in mind: a low altitude airspace simulator, a world model in a model based agent and a metaphysical approach to artificial intelligence.

I'll briefly describe each then explain which have a place within the _current_ iteration of Horizon.

### Low Altitude Airspace Simulator
The GIS platforms I have experience with excel at making 2D maps and 3D models of systems that operate at high-altitudes such as fixed-wing commerical aircraft and satellites. However, they are not very good at modeling the low altitude airspace where drones operate and terrain matters.

In this context Horizon is a GIS platform optimized for modeling, simulating, and visualizing drone operations.

### World Model in a Model Based Agent
In "Artificial Intelligence: A Modern Approach" the authors define a model-based agent as an agent that uses its sensors and knowledge of how the world changes to keep track of the state of the world.

In this context, Horizon is the world model component of a model-based agent, specifically an agent that operates a drone.

### A Metaphysical Approach To Artificial Intelligence
Ever since I started studying AI I've been possessed by a particular train of thought:

An agent is intelligent if it acts rationally. An agent acts rationally if, given a goal, a set of capabilities, and some knowledge of the world, it acts in the way most likely to achieve its goal given its knowledge and capabilities. To possess knowledge of the world, an agent must understand the world on its own terms. I call this a "metaphysical" understanding of the world for reasons too complex to explain here. Unfortunately, contemporary AI systems do not understand the world on its own terms. Their amazing predictive accuracy conceals a fundamental blindness to the world they make predictions about. This blindness explains several of the known and despised flaws in contemporary AI systems. In order to build true AI, and better AI systems in general, a metaphysical approach to AI must be adopted, one in which machines are built that understand reality on its own terms.

I think there's some real meat to this thesis, and given the time I'm sure I could expound upon my ideas at book length. If nothing else, doing so would help me articulate my thoughts.

In this context, Horizon is a system which implements a metaphysical approach to AI by creating and maintaining an ontologically faithful model of a drone's operating environment.

### Conclusion
I'm putting my foot down right here. The current iteration of Horizon, the iteration I'm working on as a portfolio project, refers to the first project, not the second nor the third. 

I am building a data platform to model real time drone operations in low altitude airspace. I am not going to stick horizon models inside of autonomous agents. I am not going to write _A Metaphysical Approach to Artificial Intelligence_. I would like to do both of those things in the future. __I WILL__ do both of those things in the future. But I am not going to do them now. 

In order to distinguish Horizon, my portfolio project, from Horizon, my ill-defined ambitions, I will refer to the current iteration of the project as Horizon Mk I. The next iteration of Horizon that beyond the scope of my portfolio project will be named Horizon Mk II, and so on.


## Goals

The primary goal of the present iteration of Horizon is to get me a job. In this case, the journey truly is more important the destination. I've split the project up into 6 versions, each of which involes building a more complex system than the last. 

- v0.1 Simple Application
- v0.2 Networked Application
- v0.3 Event-Driven Application
- v0.4 Data Platform
- v0.5 Cloud Data Platform
- v1.0 Production Ready Cloud Data Platform

That said, the destination is important as well. The primary goal of the project from that perspective is to build a production-ready, cloud-deployed data platform that models and visualizes drone operations in real time by integrating multiple heterogeneous data sources. 
