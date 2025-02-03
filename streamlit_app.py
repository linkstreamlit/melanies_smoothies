import streamlit as st
import pandas as pd
#from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
import requests

st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("""Choose the fruits you want in your custom smoothie!""")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your smoothie will be: ', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch data from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert the Snowpark dataframe to a pandas dataframe
pd_df = my_dataframe.to_pandas()

# Multiselect widget for ingredient selection
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df['FRUIT_NAME'].tolist(),  # Use the pandas dataframe
    max_selections=5
)

# Define ingredients_string so it's in scope even if the list is empty
ingredients_string = ""

if ingredients_list:
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Debugging: Print the value and type of search_on
        st.write('Debug: search_on value:', search_on)
        st.write('Debug: search_on type:', type(search_on))

        st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

        st.subheader(fruit_chosen + ' Nutrition Information')
        
        # Make API request and handle potential errors
        try:
            smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + str(search_on))
            smoothiefroot_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data for {fruit_chosen}: {e}")

# Prepare SQL insert statement using parameterized query
my_insert_stmt = """
    INSERT INTO smoothies.public.orders (ingredients, name_on_order)
    VALUES (%s, %s)
"""

time_to_insert = st.button('Submit Order')
if time_to_insert:
    session.cursor().execute(my_insert_stmt, (ingredients_string.strip(), name_on_order.strip()))
    st.success('Your Smoothie is Ordered!', icon="✅")
