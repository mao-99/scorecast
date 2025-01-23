# Step 1: import webdriver - webdrivers
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import pandas as pd
import os
import json


#initialize webdriver
driver = webdriver.Chrome()

#array to hold the links to each of the 5 leagues
leagues = [
            # 'https://www.flashscore.com/football/england/premier-league/archive/',
            # 'https://www.flashscore.com/football/france/ligue-1/archive/', 
            # 'https://www.flashscore.com/football/germany/bundesliga/archive/',
            # 'https://www.flashscore.com/football/italy/serie-a/archive/',
            'https://www.flashscore.com/football/spain/laliga/archive/',
            'https://www.flashscore.com/football/usa/mls/archive/',
            'https://www.flashscore.com/football/usa/usl-championship/archive/',
            'https://www.flashscore.com/football/europe/champions-league/archive/',
            'https://www.flashscore.com/football/europe/europa-league/archive/'
            ]



def is_button_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "event__more.event__more--static"))
        )
        return True
    except TimeoutException:
        return False

#using a loop, we iterate through each league
for league in leagues:
    #using a try-except block to handle exceptions
    try:
        driver.get(league)

        #we verify the league's archive was loaded by getting the page's title
        print(driver.title)

        #sleep for 1 second
        time.sleep(1)

        #create directory to house data
        season_data_dir = "season_data"
        os.makedirs(season_data_dir, exist_ok=True)

        #at this point, we are at the archive list of the league. 
        #what we need to do now is find each season's element
        seasons = driver.find_elements(by=By.CLASS_NAME, value='archive__season')

        #use a loop to visit each season the seasons array
        #notice that we start counting from index 1 because of the way the website's elements are structured

        for season in seasons[1:11]:
            season_text = season.text.strip().lower().replace(' ', '_')
            season_filename = f'game_data_{season_text.replace('/', '_')}.json'
            season_filepath = os.path.join(season_data_dir, season_filename)

            #we find the link element using the find_element() method, and then use get_attribute() to extract its url
            season_link = season.find_element(by=By.CLASS_NAME, value='archive__text--clickable')
            season_url = season_link.get_attribute('href')

            #after extracting each season's url, use the driver to visit the season url in a different window
            #to open a new window using selenium, we need to first create the new window, then switch context to our new window, 
            #then visit the link in our new window. After finishing, we close that window and switch context back to original window
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(season_url)

            # at this point, we have opened the season's url, and now we want to get the game results
            time.sleep(1)

            #we find the results element, and use selenium to click it inside a try-except block
            try:
                #use explicit wait for up to 4 seconds for 'results' element
                results_element = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CLASS_NAME, 'tabs__tab.results')))
                #after its clickable, we use selenium's driver to click the element
                driver.execute_script('arguments[0].click();', results_element)
                time.sleep(1)

                #after opening the results of a season, we want to load all results on the page by continuously clicking on the 'show more' button
                try:
                    while is_button_present(driver):
                        try:
                            # Wait for 'show more matches' button to be clickable
                            button_element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "event__more.event__more--static"))
                            )

                            #click the button 
                            driver.execute_script('arguments[0].click();', button_element)
                            
                            #after clicking, wait 1 second and click again
                            time.sleep(1)

                        except Exception as e:
                            print("Error occured clicking on button to show more matches")
                    
                    #Now we have shown all results in a season.
                    #Now, we get the links of each individual match
                    allMatches = driver.find_elements(by=By.CLASS_NAME, value="eventRowLink")

                    #We use a for loop to go through each match, clicking and processing each match
                    for match in allMatches:
                        #when we click on a match link on flashscore.com, the match details gets opened in a pop up window
                        #to properly handle window switching, we need to get the original window handle
                        original_window = driver.current_window_handle

                        driver.execute_script("arguments[0].click()", match)

                        #we wait until the popup window opens before switching windows
                        try:
                            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(3))

                            #from above, we wait until the popup has been opened, then we switch windows

                            #switch to the popup window
                            driver.switch_to.window(driver.window_handles[-1])

                            #now we're on the popup window
                            #after popup window is opened, we wait for the body to be populated
                            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

                            #Now we find and click on the game stats element 
                            try:
                               #now, I want to click on the stats tab
                                stats_check = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[7]/div/a[2]')))
                                stats_element = driver.find_element(by=By.CSS_SELECTOR, value="a[href='#/match-summary/match-statistics']")

                                driver.execute_script('arguments[0].click();', stats_element)
                                time.sleep(4)  # Pause to load the content in the stats tab


                                # Now, lets make a dataframe from the stats were getting:
                                # Date, time, comp, round, day, venue,Home Team Name, Away Team Name, Home Team Goals, Away team goals, possession, home team goal attempts, away team goal attempts, home team shots on target 
                                # away team shots on target, home team shots off goal, away team shots off goal, home team blocked shots, away team blocked shots, home team goalkeeper saves, away team goalkeeper saves
                                

                                # For this, I will create a dataframe and scrape the content into all the equivalent columns/field, then I will open a csv file and append the 
                                # \ dataframe to the csv

                                # Alternatively, I can search for all stats divs, then based on the contents I can create a pd and then push it to the csv file

                                # Dictionary to hold onto the values
                                gameData = {}
                                league_and_round_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[3]/div/span[3]/a')))
                                league_and_round_text = league_and_round_element.text

                                league_and_round_array = league_and_round_text.split(' - ')

                                gameData['comp'] = league_and_round_array[0]
                                gameData['round'] = league_and_round_array[1]

                                home_team_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[4]/div[2]/div[3]/div[2]/a")))
                                away_team_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[4]/div[4]/div[3]/div[1]/a")))
                                
                                home_team_text = home_team_element.text
                                away_team_text = away_team_element.text

                                gameData['home_team'] = home_team_text
                                gameData['away_team'] = away_team_text

                                home_goals_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[4]/div[3]/div/div[1]/span[1]")))
                                away_goals_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[4]/div[3]/div/div[1]/span[3]")))

                                home_goals_text = home_goals_element.text
                                away_goals_text = away_goals_element.text

                                gameData['home_goals'] = home_goals_text
                                gameData['away_goals'] = away_goals_text


                                date_and_time_element = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[4]/div[1]/div')))

                                date_and_time_text = date_and_time_element.text

                                date_and_time_array = date_and_time_text.split(' ')
                                
                                gameData['date'] = date_and_time_array[0]
                                gameData['time'] = date_and_time_array[1]
                                # First, I will find all the stats
                                stats_section = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "section"))
                                )
                                
                                # Find all stat rows
                                stat_rows = stats_section.find_elements(By.CSS_SELECTOR, "[class*='wcl-category_ITphf']")
                                
                                stats = {}
                                for row in stat_rows:
                                    # Get the category name
                                    home_value = row.find_element(By.CSS_SELECTOR, "[class*='wcl-homeValue_']").text
                                    
                                    # Extract the stat title (e.g., "Ball Possession")
                                    stat_title = row.find_element(By.CSS_SELECTOR, "[class*='wcl-category_']").text
                                    
                                    # Extract away team stat value
                                    away_value = row.find_element(By.CSS_SELECTOR, "[class*='wcl-awayValue_']").text
                                    
                                    # Print or save the extracted data

                                    # print(f"Stat: {stat_title}, Home: {home_value}, Away: {away_value}")

                                    # I can directly add the stats to the gameData dictionary, then append gameData to csv file.

                                    stat_title = stat_title.lower().replace(' ', '_')

                                    gameData[f'home_{stat_title}'] = home_value
                                    gameData[f'away_{stat_title}'] = away_value
                                    
                                #Here, I want to open my csv file and write the gameData into the csv so I can open it with pandas sometime in the future to clean the data

                                #Actually, a json format will be better considering my data
                                # Now, append the gameData to a JSON file
                                json_filename = 'game_stats.json'

                                # Check if the JSON file exists and read existing data
                                if os.path.exists(season_filepath):
                                    with open(season_filepath, 'r') as file:
                                        existing_data = json.load(file)
                                else:
                                    existing_data = []

                                # Append new game data to the existing data
                                existing_data.append(gameData)

                                # Write the updated data back to the JSON file
                                with open(season_filepath, 'w') as file:
                                    json.dump(existing_data, file, indent=4)

                                print("This is the appended data: ", gameData)

                                print(f"Data appended to {json_filename} successfully.")

                                

                            except Exception as e:
                                print(f"Error interacting with popup: {str(e)}")

                            # Close the popup window
                            driver.close()

                            # Switch back to the original window
                            driver.switch_to.window(original_window)

                            time.sleep(2)

                        except Exception as e:
                            print(f'Error getting match popup: {str(e)}')   
                    print("Finished loading all matches ")                         

                except Exception as e:
                    print(f'Error getting results from results section: {str(e)}')
                    print(f"An error occurred while processing {season_url}: {str(e)}")

            except Exception as e:
                print("Error clicking results element: ", e)
                print(f"An error occurred while processing {season_url}: {str(e)}")
            
            finally:
                # Close the current tab and switch back to the main tab if the window handle exists
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
               
    except Exception as e:
        print("Error accessing league from leagues array", e)

driver.quit()
print("WebDriver session terminated.")