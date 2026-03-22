UnoBHAi
=======

A Telegram bot for playing the UNO cards game

Description
-----------

.. image:: https://i.ibb.co/XfrRt1d9/photo-2025-08-19-14-00-28.jpg
   :alt: UnoBHAi

UnoBHAi is a Telegram bot that allows users to play the famous UNO card game directly in the chat. The bot manages the game, distributes the cards, and enforces the rules, providing a fun and interactive experience.

----------------------------

Features
--------

- Creation of game rooms
- Automatic card distribution
- Turn management
- Enforcement of UNO game rules
- Support for Telegram commands to interact with the bot

How to use
----------

- Add the bot `@OnoBHAiBot <https://t.me/OnoBHAiBot>`_
- Create a game room with the command ``/new``
- Wait for other players to join the room via the button or the command ``/join``
- Start the game with the command ``/start`` or via the button
- Reply ``/remove`` to a player's message to remove from game
- Have fun playing UNO!
- If you want to customize the game such as cards and rules, use the command ``/settings``

How to run the bot locally
--------------------------

- Clone the repository:

  ::

      git clone https://github.com/nasirul786/UnoBHAi.git

- Create a virtual environment:

  ::

      python -m venv venv

- Activate the virtual environment:

  ::

      source venv/bin/activate

- Install the dependencies:

  ::

      pip install .

- Copy the ``config-example.py`` file to ``config.py`` and edit it

- Run the bot:

  ::

      python -m UnoBHAi

Contributions
-------------

Contributions are welcome! Feel free to open an issue or submit a pull request.

License
-------

This project is licensed under the MIT license. See the LICENSE file for more information.