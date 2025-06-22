--// Load Rayfield 
local Rayfield = loadstring(game:HttpGet('https://sirius.menu/rayfield'))()

--// Services
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local Camera = Workspace.CurrentCamera
local LocalPlayer = Players.LocalPlayer

--// Settings
local aimbotEnabled = false
local maxDistance = 100
local aimPart = "Head"
local fovRadius = 90
local showFOV = true

--// ESP Settings
local espEnabled = false
local showNames = true
local showBoxes = true
local showDistances = true
local espObjects = {}

--// FOV Circle
local fovCircle = Drawing.new("Circle")
fovCircle.Color = Color3.fromRGB(255, 50, 50)
fovCircle.Thickness = 1.5
fovCircle.Filled = false
fovCircle.Radius = fovRadius
fovCircle.Visible = showFOV
fovCircle.Position = Vector2.new(Camera.ViewportSize.X / 2, Camera.ViewportSize.Y / 2)

RunService.RenderStepped:Connect(function()
 fovCircle.Position = Vector2.new(Camera.ViewportSize.X / 2, Camera.ViewportSize.Y / 2)
 fovCircle.Radius = fovRadius
 fovCircle.Visible = aimbotEnabled and showFOV
end)

--// Target Finder
local function getClosestTargetInFOV()
 local closest, shortestDist = nil, math.huge
 local screenCenter = Vector2.new(Camera.ViewportSize.X / 2, Camera.ViewportSize.Y / 2)

 for _, player in ipairs(Players:GetPlayers()) do
  if player ~= LocalPlayer and player.Character and player.Character:FindFirstChild(aimPart) then
   local part = player.Character[aimPart]
   local screenPos, onScreen = Camera:WorldToViewportPoint(part.Position)
   local distFromCenter = (Vector2.new(screenPos.X, screenPos.Y) - screenCenter).Magnitude
   local worldDist = (part.Position - LocalPlayer.Character.HumanoidRootPart.Position).Magnitude

   if onScreen and distFromCenter <= fovRadius and worldDist <= maxDistance and player.Character.Humanoid.Health > 0 then
    if distFromCenter < shortestDist then
     shortestDist = distFromCenter
     closest = player
    end
   end
  end
 end

 return closest
end

--// Aimbot Logic
RunService.RenderStepped:Connect(function()
 if not aimbotEnabled then return end

 local target = getClosestTargetInFOV()
 if target and target.Character and target.Character:FindFirstChild(aimPart) then
  local pos = target.Character[aimPart].Position + Vector3.new(0, 0.85, 0)
  Camera.CFrame = CFrame.new(Camera.CFrame.Position, pos)
 end
end)

--// ESP Functions
local function clearESP()
 for _, drawings in pairs(espObjects) do
  for _, obj in pairs(drawings) do
   if typeof(obj) == "Instance" then continue end
   obj:Remove()
  end
 end
 espObjects = {}
end

local function createESP(player)
 if player == LocalPlayer or not player.Character then return end

 local box = Drawing.new("Square")
 box.Color = Color3.fromRGB(255, 0, 0)
 box.Thickness = 1
 box.Filled = false

 local name = Drawing.new("Text")
 name.Size = 13
 name.Center = true
 name.Outline = true
 name.Color = Color3.new(1, 1, 1)

 local distance = Drawing.new("Text")
 distance.Size = 12
 distance.Center = true
 distance.Outline = true
 distance.Color = Color3.new(1, 1, 1)

 espObjects[player] = {Box = box, Name = name, Distance = distance}
end

RunService.RenderStepped:Connect(function()
 if not espEnabled then
  clearESP()
  return
 end

 for _, player in pairs(Players:GetPlayers()) do
  if player == LocalPlayer or not player.Character or not player.Character:FindFirstChild("HumanoidRootPart") then
   if espObjects[player] then
    for _, obj in pairs(espObjects[player]) do
     obj.Visible = false
    end
   end
   continue
  end

  if not espObjects[player] then
   createESP(player)
  end

  local hrp = player.Character.HumanoidRootPart
  local head = player.Character:FindFirstChild("Head")
  if not head then continue end

  local pos, onscreen = Camera:WorldToViewportPoint(hrp.Position)
  local headPos = Camera:WorldToViewportPoint(head.Position + Vector3.new(0, 0.5, 0))
  local feetPos = Camera:WorldToViewportPoint(hrp.Position - Vector3.new(0, 2.5, 0))

  local boxHeight = math.abs(headPos.Y - feetPos.Y)
  local boxWidth = boxHeight / 2
  local box = espObjects[player].Box
  local name = espObjects[player].Name
  local distance = espObjects[player].Distance

  if onscreen then
   if showBoxes then
    box.Size = Vector2.new(boxWidth, boxHeight)
    box.Position = Vector2.new(pos.X - boxWidth/2, pos.Y - boxHeight/2)
    box.Visible = true
   else
    box.Visible = false
   end

   if showNames then
    name.Text = player.Name
    name.Position = Vector2.new(pos.X, pos.Y - boxHeight / 2 - 15)
    name.Visible = true
   else
    name.Visible = false
   end

   if showDistances then
    local dist = math.floor((hrp.Position - LocalPlayer.Character.HumanoidRootPart.Position).Magnitude)
    distance.Text = tostring(dist) .. "m"
    distance.Position = Vector2.new(pos.X, name.Position.Y + 15)
    distance.Visible = true
   else
    distance.Visible = false
   end
  else
   box.Visible = false
   name.Visible = false
   distance.Visible = false
  end
 end
end)

--// Hitbox Extender
local function applyHitboxExtender()
 for _, player in ipairs(Players:GetPlayers()) do
  if player ~= LocalPlayer then
   local function extendHitbox(char)
    local hrp = char:FindFirstChild("HumanoidRootPart")
    if hrp then
     hrp.Size = Vector3.new(15, 15, 15)
     hrp.Transparency = 0.5
     hrp.BrickColor = BrickColor.new("Really red")
     hrp.Material = Enum.Material.ForceField
    end
   end

   if player.Character then
    extendHitbox(player.Character)
   end

   player.CharacterAdded:Connect(function(char)
    repeat task.wait() until char:FindFirstChild("HumanoidRootPart")
    extendHitbox(char)
   end)
  end
 end

 Players.PlayerAdded:Connect(function(player)
  player.CharacterAdded:Connect(function(char)
   repeat task.wait() until char:FindFirstChild("HumanoidRootPart")
   local hrp = char:FindFirstChild("HumanoidRootPart")
   if hrp then
    hrp.Size = Vector3.new(15, 15, 15)
    hrp.Transparency = 0.5
    hrp.BrickColor = BrickColor.new("Really red")
    hrp.Material = Enum.Material.ForceField
   end
  end)
 end)
end

-- Improved FPS Boost Function
local function improvedFPSBoost()
    local Lighting = game:GetService("Lighting")
    local Workspace = game:GetService("Workspace")
    local Terrain = Workspace:FindFirstChildOfClass("Terrain")

    -- Disable lighting effects
    for _, effect in pairs(Lighting:GetChildren()) do
        if effect:IsA("BlurEffect")
        or effect:IsA("SunRaysEffect")
        or effect:IsA("ColorCorrectionEffect")
        or effect:IsA("BloomEffect")
        or effect:IsA("DepthOfFieldEffect") then
            effect.Enabled = false
        end
    end

    -- Simplify terrain water properties
    if Terrain then
        Terrain.WaterWaveSize = 0
        Terrain.WaterWaveSpeed = 0
        Terrain.WaterReflectance = 0
        Terrain.WaterTransparency = 0
    end

    -- Turn off global shadows
    Lighting.GlobalShadows = false

    -- Increase fog distance (reduce fog)
    Lighting.FogEnd = 9e9

    -- Reduce quality level to lowest
    pcall(function()
        settings().Rendering.QualityLevel = "Level01"
    end)

    -- Remove textures and materials that cause lag
    for _, obj in pairs(workspace:GetDescendants()) do
        if obj:IsA("Decal") or obj:IsA("Texture") then
            obj.Transparency = 1
        elseif obj:IsA("ParticleEmitter") or obj:IsA("Trail") then
            obj.Enabled = false
        elseif obj:IsA("MeshPart") or obj:IsA("Part") or obj:IsA("UnionOperation") then
            obj.Material = Enum.Material.Plastic
            obj.Reflectance = 0
        end
    end

    -- Remove shadows on players
    for _, player in pairs(game.Players:GetPlayers()) do
        local character = player.Character
        if character then
            for _, part in pairs(character:GetChildren()) do
                if part:IsA("BasePart") then
                    part.CastShadow = false
                end
            end
        end
    end
end

--// Rayfield UI
local Window = Rayfield:CreateWindow({
 Name = "Live Aimbot Hub + ESP",
 LoadingTitle = "Loading...",
 LoadingSubtitle = "Mobile Optimized Script",
 ConfigurationSaving = { Enabled = false },
 Discord = { Enabled = false },
 KeySystem = false
})

-- Aimbot Tab
local AimbotTab = Window:CreateTab("Aimbot", 4483362458)
AimbotTab:CreateSection("Controls")

AimbotTab:CreateToggle({
 Name = "Enable Aimbot (Live Tracking)",
 CurrentValue = false,
 Callback = function(Value)
  aimbotEnabled = Value
 end
})

AimbotTab:CreateSlider({
 Name = "Lock Distance",
 Range = {10, 500},
 Increment = 10,
 Suffix = " studs",
 CurrentValue = maxDistance,
 Callback = function(Value)
  maxDistance = Value
 end
})

AimbotTab:CreateSlider({
 Name = "FOV Radius",
 Range = {40, 200},
 Increment = 5,
 Suffix = " px",
 CurrentValue = fovRadius,
 Callback = function(Value)
  fovRadius = Value
 end
})

AimbotTab:CreateDropdown({
 Name = "Aim Part",
 Options = {"Head", "Torso"},
 CurrentOption = "Head",
 Callback = function(option)
  aimPart = (option == "Torso") and "HumanoidRootPart" or "Head"
 end
})

AimbotTab:CreateToggle({
 Name = "Show FOV Circle",
 CurrentValue = showFOV,
 Callback = function(Value)
  showFOV = Value
 end
})

-- ESP Tab
local ESPTab = Window:CreateTab("ESP", 4483362458)
ESPTab:CreateSection("Visuals")

ESPTab:CreateToggle({
 Name = "Enable ESP",
 CurrentValue = espEnabled,
 Callback = function(Value)
  espEnabled = Value
  if not Value then
   clearESP()
  end
 end
})

ESPTab:CreateToggle({
 Name = "Show Boxes",
 CurrentValue = showBoxes,
 Callback = function(Value)
  showBoxes = Value
 end
})

ESPTab:CreateToggle({
 Name = "Show Names",
 CurrentValue = showNames,
 Callback = function(Value)
  showNames = Value
 end
})

ESPTab:CreateToggle({
 Name = "Show Distances",
 CurrentValue = showDistances,
 Callback = function(Value)
  showDistances = Value
 end
})

-- Extra Tab
local ExtraTab = Window:CreateTab("Extra", 4483362458)
ExtraTab:CreateSection("Other Tools")

ExtraTab:CreateButton({
 Name = "Kill Self",
 Callback = function()
  if LocalPlayer.Character and LocalPlayer.Character:FindFirstChild("Humanoid") then
   LocalPlayer.Character.Humanoid.Health = 0
  end
 end
})

ExtraTab:CreateButton({
 Name = "Enable Hitbox Extender (Use Only Once More Then That Will Crash The Game)",
 Callback = function()
  loadstring(game:HttpGet('https://pastebin.com/raw/6zXxnvRE'))()
 end
})

ExtraTab:CreateButton({
 Name = "Improved FPS Boost",
 Callback = function()
  improvedFPSBoost()
 end
})
