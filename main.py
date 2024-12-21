from run import Bot
import asyncio


async def main():
    # Initialize and run the bot
    await Bot.initialize()
    await Bot.run()

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
