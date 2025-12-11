-- LuCI Tuple ECH Worker Controller
-- Copyright (C) 2024

module("luci.controller.ech-workers", package.seeall)

function index()
    if not nixio.fs.access("/etc/config/ech-workers") then
        return
    end
    
    entry({"admin", "services", "ech-workers"}, 
          cbi("ech-workers"), 
          _("Tuple ECH Worker"), 
          90).dependent = true
    
    entry({"admin", "services", "ech-workers", "status"},
          call("action_status")).leaf = true
    
    entry({"admin", "services", "ech-workers", "control"},
          call("action_control")).leaf = true
    
    entry({"admin", "services", "ech-workers", "log"},
          call("action_log")).leaf = true
end

function action_status()
    local sys = require "luci.sys"
    local http = require "luci.http"
    
    local running = sys.call("pgrep -f ech-workers >/dev/null") == 0
    
    http.prepare_content("application/json")
    http.write_json({
        running = running
    })
end

function action_log()
    local sys = require "luci.sys"
    local http = require "luci.http"
    
    local log = sys.exec("logread -e ech-workers 2>/dev/null | tail -n 100")
    
    http.prepare_content("text/plain")
    http.write(log or "无日志")
end

function action_control()
    local sys = require "luci.sys"
    local http = require "luci.http"
    
    local action = http.formvalue("action")
    local result = { success = false, message = "" }
    
    if action == "start" then
        sys.call("/etc/init.d/ech-workers start >/dev/null 2>&1")
        result.success = true
        result.message = "启动命令已执行"
    elseif action == "stop" then
        sys.call("/etc/init.d/ech-workers stop >/dev/null 2>&1")
        result.success = true
        result.message = "停止命令已执行"
    elseif action == "restart" then
        sys.call("/etc/init.d/ech-workers restart >/dev/null 2>&1")
        result.success = true
        result.message = "重启命令已执行"
    else
        result.message = "未知操作"
    end
    
    http.prepare_content("application/json")
    http.write_json(result)
end
