from asyncio import sleep
from base64 import b64decode
from datetime import datetime, timedelta
from io import BytesIO
from logging import error
from random import randint, shuffle
from disnake import ApplicationCommandInteraction, Embed, File
from disnake.ext.commands import (
    Cog,
    Param,
    slash_command,
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


class Miscellaneous(Cog, name="misc.imagine"):
    def __init__(self, bot):
        self.bot = bot

    """ COMMANDS """

    @slash_command(
        name="imagine", description="Imagine a gallery of art from your input"
    )
    async def imagine_slash_command(
        self,
        inter: ApplicationCommandInteraction,
        query: str = Param(
            description="The query to generate the image(s) from",
            min_length=4,
            max_length=500,
        ),
        num_images: int = Param(
            1, description="The number of images to generate", min_value=1, max_value=9
        ),
    ):
        em: Embed = Embed(
            colour=randint(0, 0xFFFFFF),
            description=f'🎨 - Generating your gallery of art from your input: "{query}", please wait...\n\n*(This can take up to 2 minutes)*',
        )
        await inter.response.send_message(embed=em)

        firefox_options = Options()
        firefox_options.add_argument("--headless")

        with webdriver.Firefox(options=firefox_options) as driver:
            try:
                images = None
                driver.delete_all_cookies()
                driver.get("https://www.craiyon.com/")
                wait = WebDriverWait(driver, 20)
                await sleep(3)

                try:
                    driver.find_element(By.ID, "qc-cmp2-ui").find_element(
                        By.CLASS_NAME, "qc-cmp2-summary-buttons"
                    ).find_elements(By.TAG_NAME, "button")[1].click()
                except NoSuchElementException:
                    pass

                wait.until(EC.element_to_be_clickable((By.ID, "prompt")))
                prompt = driver.find_element(By.ID, "prompt")
                prompt.send_keys(query)
                prompt.send_keys(Keys.ENTER)
                now = datetime.now()

                while now - datetime.now() < timedelta(seconds=130):
                    try:
                        images = driver.find_element(
                            By.XPATH, "//div[@class='grid grid-cols-3 gap-2']"
                        )
                        break
                    except NoSuchElementException:
                        await sleep(5)

                    if images:
                        break
            except Exception as e:
                driver.save_screenshot("error.png")
                error(e)
            finally:
                if images is None:
                    em.description = "🎨 - An error occurred while generating your gallery of art, please try again later."
                    return self.bot.loop.create_task(
                        inter.edit_original_message(embed=em)
                    )

            images = images.find_elements(
                By.XPATH, "//div[@class='grid grid-cols-3 gap-2']//img"
            )
            shuffle(images)
            files = []

            for x in range(num_images):
                files.append(
                    File(
                        BytesIO(
                            b64decode(
                                images[x]
                                .get_attribute("src")
                                .replace("data:image/jpeg;base64,", "")
                            )
                        ),
                        filename=f"ai_generated_{x}.jpeg",
                    )
                )

        em.description = f"🎨 - **Your gallery of art is ready!**"
        self.bot.loop.create_task(inter.edit_original_message(embed=em, files=files))


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
