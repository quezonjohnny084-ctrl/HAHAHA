-- 1. Your custom Lua code or modifications go here
print("Custom payload initialized successfully!")

-- 2. Call the original application script so the app still functions
local status, err = pcall(function()
    dofile(backend_path or "main1.lua")
end)

if not status then
    print("Error loading original main1.lua: " .. tostring(err))
end
