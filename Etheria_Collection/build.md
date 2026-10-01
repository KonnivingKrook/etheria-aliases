Build Alias Documentation
`!build start <name> [-image <url>]` - start a project in this channel (add `-confirm` to replace an existing one)
`!build image <url>` - set the project's image (`clear` to remove it)
`!build req <quota> <material>` - add or update a material requirement
`!build rm <material>` - remove a material requirement
`!build add <quantity> <material> [-n note]` - contribute materials (negative to correct a mistake)
`!build work <checks> <material> [method] [-n note]` - log successful checks or spells (negative to correct a mistake)
`!build list [log]` - show progress (add `log` for recent activity)
`!build projects` - list every open project across the server

**Examples**
`!build req 100 Adamantine` / `!build req 100 Common Wood`
`!build add 10 Adamantine -n On loan!`
`!build work 2 Common Stone Wall of Stone`

Material names can be shortened, e.g. `!build add 5 ada` for Adamantine or `!build work 1 wood` for Common Wood.