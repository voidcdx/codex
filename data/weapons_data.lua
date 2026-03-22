---	WARFRAME weapon database to be used on the wiki.
--	
--	@module			weapons/data
--	@alias			data
--	@attribution	[[User:FINNER|FINNER]]
--	@attribution	[[User:Cephalon Scientia|Cephalon Scientia]]
--	@attribution	Everyone who contributes to adding new data or updating existing values in database
---	@require		[[Module:LuaSerializer]]
--	@release		stable
--	<nowiki>

-- TODO: Since horizontal partitions are accessed programmatically, this means
-- that this module can be tailored to serve specific user localizations.
-- All we need to do is to add a locale flag in here set to mw.getCurrentFrame():preprocess('{{int:Custom-lang}}'), 
-- a separate translation table (likely JSON) for mapping canonical internal names to localized names, 
-- and replace the Name key/Trigger key/index key with the localized counterpart.
-- In theory, any database access by requiring this module should contain the 
-- proper localization based on user's interface language setting.

local data = {}

local MODULE_LOCALIZATION = mw.site.namespaces[828].name

-- Current M:Weapons/data subpages
local COOP_SLOTS = { 'primary', 'secondary', 'melee', 'archwing', 'companion', 'railjack', 'modular', 'misc' }

-- Mapping weapon slot to M:Weapons/data subpage
local SLOTS_MAP = {
	primary = 'primary',
	secondary = 'secondary',
	melee = 'melee',

	archwing = 'archwing',
	['archgun'] = 'archwing',
	['archmelee'] = 'archwing',
	['archgun (atmosphere)'] = 'archwing',

	companion = 'companion',
	['robotic'] = 'companion',
	['hound'] = 'companion',
	['beast'] = 'companion',

	railjack = 'railjack',
	['railjack turret'] = 'railjack',
	['railjack ordnance'] = 'railjack',

	modular = 'modular',
	['amp'] = 'modular',
	['kitgun'] = 'modular',
	['zaw'] = 'modular',

	misc = 'misc',
	['emplacement'] = 'misc',
	['gear'] = 'misc',
	['nech-melee'] = 'misc',
	['unique'] = 'misc',
	['vehicle'] = 'misc',
}

-- Defining default metatable values
local dbMetatable = {
	-- Page title of database
	_pageName = 'Weapons/data'
}
dbMetatable._pageTitle = MODULE_LOCALIZATION..':'..dbMetatable._pageName

---	Defining custom looping behavior with pairs() to iterate over multiple 
--	partitions while acting as one database table.
--	@function		data.__pairs
--	@param			{table} self Table self-reference
--	@return			{function} Iterator function
--	@return			{table} Contains key-pair values of slot names to corresponding horizontal partition
dbMetatable.__pairs = function(self)
		local temp = {}
		local slots = COOP_SLOTS
		
		for i, slot in ipairs(slots) do
			temp[i] = mw.loadData(getmetatable(self)._pageTitle..'/'..slot)
		end
		
		function next(t, key)
			return pairs(t)(t, key)
		end

		function __next(t, key)
			if not key then
				return next(t[1])
			else
				for i = 1, #t - 1 do
					if t[i][key] then
						if next(t[i], key) then
							return next(t[i], key)
						else
							return next(t[i + 1])
						end
					end
				end
				return next(t[#t], key)
			end
		end

		return __next, temp, nil
	end

---	Supporting indexing by slot name (returns array of weapon entries) or weapon name
--	(returns a weapon entry).
--	@function		data.__index
--	@param			{table} self Table self-reference
--	@param			{string} key Index key
--	@return			{table}
dbMetatable.__index = function(self, key)
		if (type(key) == 'number') then return nil end
		
		-- Indexing by slot
		if key and SLOTS_MAP[key:lower()] then
			return mw.loadData(getmetatable(self)._pageTitle..'/'..SLOTS_MAP[key:lower()])
		end
		
		local slots = COOP_SLOTS
		
		-- Indexing by weapon name
		local weapon
		for _, slot in ipairs(slots) do
			weapon = mw.loadData(getmetatable(self)._pageTitle..'/'..slot)[key]
			
			if weapon then
				return weapon
			end
		end
		return nil
	end

---	For changing which type of database to pull data from.
--	If you want to switch to a different database in the same script, must require()
--	a new instance of M:Weapons/data.
--	@function		__call
--	@usage			require('Module:Weapons/data')(true)
--	@param			{table} self Table self-reference
--	@param			{table} args Argument table
--	@return			{table} Database table
dbMetatable.__call = function(self, args)
		-- Define logic for additional named arguments before the return statement
		-- TODO: We can take advantage of calling a database table by adding additional arguments
		-- for filtering out content.
		return self
	end

---	Serializes database tables into a single string with no functions and metatables.
--	@function		__tostring
--	@param			{table} self Table self-reference
--	@return			{string} Serialized database
dbMetatable.__tostring = function(self)
		return require('Module:LuaSerializer')._serialize(getmetatable(self)._pageName)
	end

setmetatable(data, dbMetatable)

return data