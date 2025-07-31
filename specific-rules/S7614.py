import asyncio

async def lambda_handler(event, context): # Noncompliant 
  ...

async def another_function(event, context): # Compliant
  ...
